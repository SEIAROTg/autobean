from typing import List, Dict, Optional, Tuple, Set
from collections import namedtuple, defaultdict
from decimal import Decimal
from beancount.core.data import Directive, Open, Close, Custom, Transaction, Posting
from beancount.core import realization, inventory
import beancount.core.account
from autobean.utils.error_logger import ErrorLogger
from autobean.share.policy import Policy
from autobean.share import utils


def split_postings(entries: List[Directive], logger: ErrorLogger) -> List[Directive]:
    plugin = SplitPostingsPlugin(logger)
    return plugin.process(entries)


AccountNotFoundError = namedtuple('AccountNotFoundError', 'source message entry')
NoApplicablePolicyError = namedtuple('NoApplicablePolicyError', 'source message entry')
InvalidDirectiveError = namedtuple('InvalidDirectiveError', 'source message entry')
InvalidSharePolicyError = namedtuple('InvalidSharePolicyError', 'source message entry')
ProportionateError = namedtuple('ProportionateError', 'source message entry')
TOLERANCE = Decimal(1e-6)


class SplitPostingsPlugin:
    logger: ErrorLogger
    named_policies: Dict[str, Policy]
    account_policies: Dict[Tuple[str, bool], Policy]  # (account, recursive) -> policy
    real_root: realization.RealAccount
    open_accounts: Set[str]

    def __init__(self, logger: ErrorLogger):
        self.logger = logger
        self.named_policies = defaultdict(Policy)
        self.account_policies = defaultdict(Policy)
        self.real_root = realization.RealAccount('')
        self.open_accounts = set()
        super().__init__()

    def process(self, entries: List[Directive]) -> List[Directive]:
        ret = []
        for entry in entries:
            if utils.is_share_policy_directive(entry):
                self.process_share_policy_definition(entry)
                entry = None
            elif utils.is_proportionate_assertion_directive(entry):
                self.process_proportionate(entry)
            elif isinstance(entry, Open):
                entry = self.process_open(entry)
            elif isinstance(entry, Close):
                self.process_close(entry)
            elif isinstance(entry, Transaction):
                entry = self.process_transaction(entry)
            if entry:
                ret.append(entry)
        return ret

    def process_share_policy_definition(self, entry: Custom):
        if len(entry.values) != 1:
            self.logger.log_error(InvalidDirectiveError(
                entry.meta, 'Share policy definition expects 1 account or string argument but {} are given'.format(len(entry.values)), entry
            ))
        elif entry.values[0].dtype == beancount.core.account.TYPE:
            # account policy
            account = entry.values[0].value
            recursive = entry.meta.get('share_recursive', True)
            if self.get_referenced_accounts(account, recursive, entry):
                policy = self.extract_policy(entry.meta, entry)
                self.account_policies[(account, recursive)].replace(policy)
        elif entry.values[0].dtype is str:
            # named policy
            policy_name = entry.values[0].value
            if not policy_name:
                self.logger.log_error(InvalidSharePolicyError(
                    entry.meta, 'Policy name cannot be empty', entry
                ))
                return
            policy = self.extract_policy(entry.meta, entry)
            # Allow changes on policies to propagate
            if 'share_policy' in entry.meta:
                self.named_policies[policy_name] = policy
            else:
                self.named_policies[policy_name].replace(policy)
        else:
            self.logger.log_error(InvalidSharePolicyError(
                entry.meta, 'Share policy must be assigned a name or applied on an account', entry
            ))

    def process_open(self, entry: Open) -> Open:
        self.open_accounts.add(entry.account)
        policy = self.extract_policy(entry.meta, entry, required=False)
        if policy:
            recursive = entry.meta.get('share_recursive', False)
            self.account_policies[(entry.account, recursive)] = policy
        open = utils.strip_meta(entry)
        return open

    def process_close(self, entry: Close):
        self.open_accounts.remove(entry.account)
    
    def prorata_selector(self, posting: Posting) -> Optional[Tuple[int, str]]:
        return (posting.account.split(':', 1)[0], posting.units.currency)

    def process_transaction(self, entry: Transaction) -> Transaction:
        transaction_policy = self.extract_policy(entry.meta, entry, required=False)
        # Split postings proportionately by party
        postings = []
        prorata_policies = {}
        for posting in entry.postings:
            prorata_selector = self.prorata_selector(posting)
            if posting.meta and posting.meta.get('share_prorata', False) == True:
                continue
            policy = self.get_posting_policy(posting, entry, transaction_policy, ignore_error=True)
            prorata_policy = prorata_policies.get(prorata_selector, None)
            if not prorata_policy:
                prorata_policy = Policy()
                prorata_policy.total_weight = Decimal(0)
                prorata_policies[prorata_selector] = prorata_policy
            for party, share in policy.items():
                if share:
                    split_amount = utils.amount_distrib(posting.units, share, policy.total_weight)
                    prorata_policy.setdefault(party, Decimal(0))
                    prorata_policy[party] += split_amount.number
                    prorata_policy.total_weight += split_amount.number

        for posting in entry.postings:
            if posting.meta and posting.meta.get('share_prorata', False) == True:
                policy = prorata_policies[self.prorata_selector(posting)]
            else:
                policy = self.get_posting_policy(posting, entry, transaction_policy)
            for party, share in policy.items():
                if share:
                    subaccount = posting.account + ':[{}]'.format(party)
                    split_posting = utils.posting_distrib(posting, share, policy.total_weight)
                    split_posting = utils.strip_meta(split_posting)
                    split_posting = split_posting._replace(
                        account=subaccount,
                    )
                    postings.append(split_posting)
        # Finalize processed postings
        entry = utils.strip_meta(entry)
        entry = entry._replace(
            postings=postings,
        )
        self.realize_transaction(entry)
        return entry

    def process_proportionate(self, entry: Custom):
        if len(entry.values) != 1:
            self.logger.log_error(InvalidDirectiveError(
                entry.meta, 'Proportionate assertion expects 1 account argument but {} are given'.format(len(entry.values)), entry
            ))
            return
        if entry.values[0].dtype != beancount.core.account.TYPE:
            self.logger.log_error(InvalidDirectiveError(
                entry.meta, 'Proportionate assertion must be applied on an account', entry
            ))
            return
        account = entry.values[0].value
        recursive = entry.meta.get('share_recursive', True)
        accounts = self.get_referenced_accounts(account, recursive, entry)
        for account in accounts:
            policy = self.extract_policy(entry.meta, entry, required=False) \
                or self.get_account_policy(account) \
                or self.named_policies.get('default', None)
            if not policy:
                self.logger.log_error(NoApplicablePolicyError(
                    entry.meta, 'No applicable share policy to proportionate assertion on account "{}"'.format(account), entry
                ))
                continue
            reference_inventory = None
            real_accounts = {
                k[1:-1]: v
                for k, v in realization.get(self.real_root, account, {}).items()
                if k[0] == '[' and k[-1] == ']'
            }
            for party, share in policy.items():
                real_account = real_accounts.get(party, None)
                if real_account is None:
                    balance = inventory.Inventory()
                else:
                    balance = real_account.balance
                if share == 0:
                    diff = balance
                else:
                    normalized_inventory = balance * (1 / share)
                    if reference_inventory is None:
                        reference_inventory = normalized_inventory
                        continue
                    else:
                        diff = abs(normalized_inventory + (-reference_inventory))
                if not diff.is_small(TOLERANCE):
                    self.logger.log_error(ProportionateError(
                        entry.meta, 'Account "{}" is disproportionate'.format(account), entry
                    ))
            # parties not in policy should have zero balance
            for party in set(real_accounts.keys()) - set(policy.keys()):
                real_account = real_accounts[party]
                if not real_account.balance.is_small(TOLERANCE):
                    self.logger.log_error(ProportionateError(
                        entry.meta, 'Account "{}" is disproportionate'.format(account), entry
                    ))

    def realize_transaction(self, entry: Transaction):
        for posting in entry.postings:
            real_account = realization.get_or_create(self.real_root, posting.account)
            real_account.balance.add_position(posting)

    def get_referenced_accounts(self, account: str, recursive: bool, entry: Directive):
        if recursive:
            accounts = [
                open_account
                for open_account in self.open_accounts
                if open_account == account or open_account.startswith(account + ':')
            ]
            if not accounts:
                self.logger.log_error(AccountNotFoundError(
                    entry.meta, 'Account "{}" is not found or inactive, as well as all its sub-accounts'.format(account), entry
                ))
        else:
            accounts = [account] if account in self.open_accounts else []
            if not accounts:
                self.logger.log_error(AccountNotFoundError(
                    entry.meta, 'Account "{}" is not found or inactive'.format(account), entry
                ))
        return accounts

    def get_account_policy(self, account: str) -> Optional[Policy]:
        policy = self.account_policies.get((account, False))
        if policy:
            return policy
        for account in utils.ancestor_accounts(account):
            policy = self.account_policies.get((account, True), None)
            if policy:
                return policy

    def get_posting_policy(self, posting: Posting, transaction: Transaction, transaction_policy: Optional[Policy], ignore_error: bool = False) -> Policy:
        policy = posting.meta and self.extract_policy(posting.meta, transaction, required=False) \
            or self.get_account_policy(posting.account) \
            or transaction_policy \
            or self.named_policies.get('default', None)
        if not policy:
            if not ignore_error:
                self.logger.log_error(NoApplicablePolicyError(
                    posting.meta or transaction.meta, 'No applicable share policy to account "{}"'.format(posting.account), transaction
                ))
            policy = Policy()
            policy.total_weight = 0
        return policy

    def extract_policy(self, meta: Dict, entry: Optional[Directive] = None, required: bool = True) -> Optional[Policy]:
        policy = Policy()
        total_weight = 0
        found = False
        for k, v in meta.items():
            if k.startswith('share-'):
                party_name = k[len('share-'):]
                if not party_name:
                    self.logger.log_error(InvalidSharePolicyError(
                        meta, 'Expect a name to share with', entry
                    ))
                elif not isinstance(v, Decimal):
                    self.logger.log_error(InvalidSharePolicyError(
                        meta, 'Expect a weight of share in decimal', entry
                    ))
                elif not party_name[0].isupper():
                    self.logger.log_error(InvalidSharePolicyError(
                        meta, 'The name to share with must start with an uppercase letter', entry
                    ))
                else:
                    found = True
                    policy[party_name] = v
                    total_weight += v
        policy.total_weight = total_weight
        if 'share_policy' in meta:
            if found:
                self.logger.log_error(InvalidSharePolicyError(
                    meta, 'Mixed use of "share_policy" and "share-" attributes', entry
                ))
            elif meta['share_policy'] not in self.named_policies:
                self.logger.log_error(InvalidSharePolicyError(
                    meta, 'Share policy "{}" does not exist'.format(meta['share_policy']), entry
                ))
            else:
                found = True
                policy = self.named_policies[meta['share_policy']]
        if required and not found:
            self.logger.log_error(InvalidSharePolicyError(
                meta, 'Expect definition of share policy', entry
            ))
        return policy if found or required else None
