from .__init__ import *
from .static_methods import _get_inner_instructions, _get_swaps, _get_in_and_out_transfer_instructions, \
    _is_fee_instruction


class JupEventParser(Coder):
    def __init__(self, idl: Idl, endpoint: str = 'https://api.mainnet-beta.solana.com'):
        self.account_info_manager = AccountInfoManager(endpoint)
        self.tokens_jup_session = TokensJupSession()
        self.price_jup_session = PriceJupSession()
        super().__init__(idl)

    def get_route_info_list(self, transaction_with_meta: EncodedTransactionWithStatusMeta):
        route_info_list = []
        for index, instruction in enumerate(transaction_with_meta.transaction.message.instructions):
            if instruction.program_id == JUPITER_V6_PROGRAM_ID:
                ix: NamedInstruction = self.instruction.parse(base58.b58decode(instruction.data))
                if ix.name in ROUTE_NAMES:
                    route_info_list.append(RouteInfo(
                        index,
                        1,
                        ix.name,
                        instruction.accounts,
                        ix.data
                    ))

        return route_info_list

    async def extract_single_route(self,
                                   transaction_with_meta: EncodedTransactionWithStatusMeta,
                                   route_info: RouteInfo):
        account_infos_dict = {}
        parsed_events = await self.get_parsed_events(transaction_with_meta, route_info)

        swap_events = [event.data for event in parsed_events if event.name == 'ParsedSwapEvent']
        fee_events = [event.data for event in parsed_events if event.name == 'ParsedFeeEvent']
        if len(swap_events) == 0:
            # Not a swap event, for example:
            # https://solscan.io/tx/5ZSozCHmAFmANaqyjRj614zxQY8HDXKyfAs2aAVjZaadS4DbDwVq8cTbxmM5m5VzDcfhysTSqZgKGV1j2A2Hqz1V
            return

        accounts_to_be_fetched = []
        [accounts_to_be_fetched.append(event.input_mint) for event in swap_events]
        [accounts_to_be_fetched.append(event.output_mint) for event in swap_events]

        if len(fee_events) > 0:
            accounts_to_be_fetched.append(fee_events[0].account)

        account_infos = await self.account_info_manager.get_account_info_json_parsed(accounts_to_be_fetched)
        for account, account_info in account_infos.items():
            account_infos_dict[account] = account_info

        swap_data = await self.parse_swap_events(account_infos_dict, swap_events)
        pass

    async def parse_swap_events(self,
                                account_infos_dict: Dict[str, AccountInfo],
                                swap_events: Sequence[ParsedSwapEvent]):
        swap_data = await asyncio.gather(
            *(self.extract_swap_data(account_infos_dict, swap_event) for swap_event in swap_events))
        return swap_data

    async def extract_swap_data(self,
                                account_infos_dict: Dict[str, AccountInfo],
                                swap_event: ParsedSwapEvent):
        amm = AMM_TYPES[str(swap_event.amm)]

        in_volume = await self.extract_volume(account_infos_dict, swap_event.input_mint, swap_event.input_amount)
        out_volume = await self.extract_volume(account_infos_dict, swap_event.output_mint, swap_event.output_amount)

        return {
            'amm': amm,
            'inSymbol': in_volume['symbol'],
            'inMint': in_volume['mint'],
            'inAmount': in_volume['amount'],
            'inAmountInDecimal': in_volume['amountInDecimal'],
            'inAmountInUSD': in_volume['amountInUSD'],
            'outSymbol': out_volume['symbol'],
            'outMint': out_volume['mint'],
            'outAmount': out_volume['amount'],
            'outAmountInDecimal': out_volume['amountInDecimal'],
            'outAmountInUSD': out_volume['amountInUSD'],
        }

    async def extract_volume(self,
                             account_infos_dict: Dict[str, AccountInfo],
                             mint: Pubkey,
                             amount: int):

        token = await self.tokens_jup_session.get_token_info(mint)
        token_price_in_usd = await self.price_jup_session.get_price_in_usd_by_mint(mint)
        token_decimals = account_infos_dict[str(mint)].value.data.parsed['info']['decimals'] \
            if str(mint) in account_infos_dict else None

        symbol = token['symbol'] if token else None
        amount_in_decimal = Decimal(amount) / (10 ** token_decimals)
        amount_in_usd = amount_in_decimal * token_price_in_usd if token_price_in_usd else None

        return {
            'token': token,
            'symbol': symbol,
            'mint': mint,
            'amount': amount,
            'amountInDecimal': amount_in_decimal,
            'amountInUSD': amount_in_usd,
        }

    async def get_parsed_events(self,
                                transaction_with_meta: EncodedTransactionWithStatusMeta,
                                route_info: RouteInfo):
        events = []
        inner_instructions = _get_inner_instructions(transaction_with_meta, route_info)
        swaps = _get_swaps(inner_instructions, route_info)
        for swap in swaps:
            transfer_instructions = _get_in_and_out_transfer_instructions(inner_instructions, swap)
            in_transfer_data = await self.get_transfer_data(transfer_instructions.in_transfers, 'in')
            out_transfer_data = await self.get_transfer_data(transfer_instructions.out_transfers, 'out')
            swap_event = ParsedEvent()
            swap_event.name = 'ParsedSwapEvent'
            swap_event.data = ParsedSwapEvent()
            swap_event.data.amm = inner_instructions[swap.instruction_index].program_id
            swap_event.data.input_mint = in_transfer_data['mint']
            swap_event.data.input_amount = in_transfer_data['amount']
            swap_event.data.output_mint = out_transfer_data['mint']
            swap_event.data.output_amount = out_transfer_data['amount']
            events.append(swap_event)

        if route_info.data.platform_fee_bps > 0:
            swap_fee = await self.get_swap_fee(route_info, inner_instructions)
            if swap_fee is None:
                return events

            fee_event = ParsedEvent()
            fee_event.name = 'ParsedFeeEvent'
            fee_event.data = ParsedFeeEvent()
            fee_event.data.account = Pubkey.from_string(swap_fee['account'])
            fee_event.data.mint = Pubkey.from_string(swap_fee['mint'])
            fee_event.data.amount = swap_fee['amount']
            events.append(fee_event)

        return events

    async def get_transfer_data(self, transfer_instructions: Sequence[InnerInstruction], transfer_type: str):
        mint = ''
        amount = 0
        for instruction in transfer_instructions:
            if (instruction.parsed['type'] == 'transferChecked' or
                    instruction.parsed['type'] == 'transferCheckedWithFee'):
                if transfer_type == 'out':
                    amount = (amount + await self.get_exact_out_amount_after_fee(
                        instruction.parsed['info'],
                        instruction.parsed['type']))
                else:
                    amount = amount + int(instruction.parsed['info']['tokenAmount']['amount'])
            else:
                amount = amount + int(instruction.parsed['info']['amount'])

        transfer_instruction = transfer_instructions[0]
        if transfer_instruction.parsed['type'] == 'transfer':
            if transfer_type == 'in':
                account = transfer_instruction.parsed['info']['destination']
            else:
                account = transfer_instruction.parsed['info']['source']

            account_infos = await self.account_info_manager.get_account_info_json_parsed(account)
            if account_infos[account] is None:
                mint = transfer_instruction.parsed['info']['mint']
            else:
                mint = account_infos[account].value.data.parsed['info']['mint']
        else:
            mint = transfer_instruction.parsed['info']['mint']

        return {'mint': mint, 'amount': amount}

    async def get_exact_out_amount_after_fee(self, info: dict, _type: str):
        # testcase 7atgF8KQo4wJrD5ATGX7t1V2zVvykPJbFfNeVf1icFv1
        # tx_id 3b6xEqa7cZv8Gbo1VjaKKuLbbXDD4g9x1m5yzGgRfSb2ozktqCrY9BtoqkSiBgnu1uwMsjBWcqqHTE2eQDy9DtTR

        # testcase 2b1kV6DkPAnxd5ixfnxCpjxmKwqjjaYmCZfHsFu24GXo
        # tx_id 2nRKszNNFYHjKevkBs9zT7gctuCS7iFVQXPfuRKX5cfCeYAQwFsZP4N6GbkXvAJSnXjMk1aNhFyYtrtDimkhJBAD

        if _type == 'transferChecked':
            fee_config = await self.account_info_manager.get_fee_config(info['mint'])
            if fee_config is None:
                return int(info['tokenAmount']['amount'])

            fee_basis_points = fee_config.newer_transfer_fee.transfer_fee_basis_points
            amount = int(info['tokenAmount']['amount'])
            fee = amount * fee_basis_points / 10_000
            return amount - fee

        return int(info['tokenAmount']['amount']) - int(info['feeAmount']['amount'])

    async def get_swap_fee(self, route_info: RouteInfo, inner_instructions: Sequence[InnerInstruction]):
        position = PLATFORM_FEE_ACCOUNTS_POSITION[route_info.name]
        fee_account = route_info.accounts[position]  # base58 ???

        for inner_instruction in inner_instructions:
            if not hasattr(inner_instruction, 'parsed') or inner_instruction.parsed is None:
                continue

            destination = inner_instruction.parsed['info']['destination']
            if _is_fee_instruction(inner_instruction, str(fee_account),
                                   destination, route_info.stack_height):
                if inner_instruction.parsed['type'] == 'transfer':
                    account_infos = await self.account_info_manager.get_account_info_json_parsed(destination)
                    mint = account_infos[destination].value.data.parsed['info']['mint']
                else:
                    mint = inner_instruction.parsed['info']['mint']

                if inner_instruction.parsed['type'] == 'transferChecked':
                    amount = inner_instruction.parsed['info']['tokenAmount']['amount']
                else:
                    amount = inner_instruction.parsed['info']['amount']

                return {'mint': mint, 'amount': amount, 'account': destination}

        return None
