from typing import Optional, List, Dict, Tuple, Set
from decimal import Decimal
from collections import namedtuple, defaultdict
import os.path
import beancount.core.account
import beancount.loader
from beancount.core import interpolate, realization, inventory
from beancount.core.data import Transaction, Posting, Custom, Open, Close, Balance, Directive
from beancount.ops import validation
from autobean.share import utils
from autobean.share.policy import Policy
from autobean.share.include_context import include_context


def plugin(entries: List[Directive], options: Dict, viewpoint: Optional[str] = None) -> Tuple[List[Directive], List]:
    is_included = include_context[0]
    if is_included:
        return entries, []
    include_context[0] = True
    errors = validation.validate(entries, options, extra_validations=validation.HARDCORE_VALIDATIONS)
    if errors:
        return entries, errors
    plugin = SharingPlugin(options, viewpoint)
    ret = plugin.process(entries)
    include_context[0] = is_included
    return ret


AccountNotFoundError = namedtuple('AccountNotFoundError', 'source message entry')
NoApplicablePolicyError = namedtuple('NoApplicablePolicyError', 'source message entry')
InvalidDirectiveError = namedtuple('InvalidDirectiveError', 'source message entry')
InvalidSharePolicyError = namedtuple('InvalidSharePolicyError', 'source message entry')
ProportionateError = namedtuple('ProportionateError', 'source message entry')
TOLERANCE = Decimal(1e-6)


class SharingPlugin:
    viewpoint: str
    entries: List[Directive]
    errors: List
    named_policies: Dict[str, Policy]
    account_policies: Dict[Tuple[str, bool], Policy]  # (account, recursive) -> policy
    open_accounts: Set[str]
    proportionate_asserted_accounts: Set[str]
    real_root: realization.RealAccount

    def __init__(self, options: Dict, viewpoint: str):
        self.viewpoint = viewpoint
        self.entries = []
        self.errors = []
        self.named_policies = defaultdict(Policy)
        self.account_policies = defaultdict(Policy)
        self.open_accounts = set()
        self.real_root = realization.RealAccount('')

    def process(self, entries: List[Directive]) -> Tuple[List[Directive], List]:
        # Pre-process entries for include directive
        included_entries = []
        for entry in entries:
            if utils.is_include_directive(entry):
                entries_local, errors_local = self.preprocess_include_directive(entry)
                included_entries.extend(entries_local)
                self.errors.extend(errors_local)
            else:
                included_entries.append(entry)

        # Process entries
        for entry in included_entries:
            if utils.is_share_policy_directive(entry):
                self.process_share_policy_definition(entry)
            elif utils.is_proportionate_assertion_directive(entry):
                self.process_proportionate(entry)
            elif utils.is_autobean_share_directive(entry):
                self.error(InvalidDirectiveError(
                    entry.meta, 'Unknown directive "{}"'.format(entry.type), entry
                ))
            elif isinstance(entry, Balance):
                self.process_balance(entry)
            elif isinstance(entry, Open):
                self.process_open(entry)
            elif isinstance(entry, Close):
                self.process_close(entry)
            elif isinstance(entry, Transaction):
                self.process_transaction(entry)
            else:
                self.entries.append(entry)
        return self.entries, self.errors

    def preprocess_include_directive(self, entry: Custom):
        if len(entry.values) < 1 or len(entry.values) > 2:
            self.error(InvalidDirectiveError(
                entry.meta, 'autobean.share.include directive expects 1 or 2 arguments but {} are given'.format(len(entry.values)), entry
            ))
            return [], []
        if len(entry.values) == 1 and entry.values[0].dtype is str:
            filename, viewpoint = entry.values[0].value, None
        elif len(entry.values) == 2 and entry.values[0].dtype is str and entry.values[1].dtype is str:
            filename, viewpoint = entry.values[0].value, entry.values[1].value
        else:
            self.error(InvalidDirectiveError(
                entry.meta, 'autobean.share.include directive should be supplied with a filename and an optional viewpoint', entry
            ))
            return [], []
        filename = os.path.join(os.path.dirname(entry.meta['filename']), filename)
        entries, errors, options = beancount.loader.load_file(filename, extra_validations=validation.HARDCORE_VALIDATIONS)
        if errors:
            errors = [
                error if error.source['lineno'] else error._replace(source=entry.meta, entry=entry)
                for error in errors
            ]
            return [], errors
        plugin = SharingPlugin(options, viewpoint)
        return plugin.process(entries)

    def process_proportionate(self, entry: Custom):
        if len(entry.values) != 1:
            self.error(InvalidDirectiveError(
                entry.meta, 'Proportionate assertion expects 1 account argument but {} are given'.format(len(entry.values)), entry
            ))
            return
        if entry.values[0].dtype is not beancount.core.account.TYPE:
            self.error(InvalidDirectiveError(
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
                self.error(NoApplicablePolicyError(
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
                    self.error(ProportionateError(
                        entry.meta, 'Account "{}" is disproportionate'.format(account), entry
                    ))
            # parties not in policy should have zero balance
            for party in set(real_accounts.keys()) - set(policy.keys()):
                real_account = real_accounts[party]
                if not real_account.balance.is_small(TOLERANCE):
                    self.error(ProportionateError(
                        entry.meta, 'Account "{}" is disproportionate'.format(account), entry
                    ))

    def process_balance(self, entry: Balance):
        # Drop balance assertions if a viewpoint is set
        if self.viewpoint is None:
            self.entries.append(entry)

    def process_share_policy_definition(self, entry: Custom):
        if len(entry.values) != 1:
            self.error(InvalidDirectiveError(
                entry.meta, 'Share policy definition expects 1 account or string argument but {} are given'.format(len(entry.values)), entry
            ))
        elif entry.values[0].dtype is beancount.core.account.TYPE:
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
                self.error(InvalidSharePolicyError(
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
            self.error(InvalidSharePolicyError(
                entry.meta, 'Share policy must be assigned a name or applied on an account', entry
            ))
    
    def process_open(self, entry: Open):
        policy = self.extract_policy(entry.meta, entry, required=False)
        if policy:
            recursive = entry.meta.get('share_recursive', False)
            self.account_policies[(entry.account, recursive)] = policy
        self.open_accounts.add(entry.account)
        open = utils.strip_meta(entry)
        self.entries.append(open)

    def get_referenced_accounts(self, account: str, recursive: bool, entry: Directive):
        if recursive:
            accounts = [
                open_account
                for open_account in self.open_accounts
                if open_account == account or open_account.startswith(account + ':')
            ]
            if not accounts:
                self.error(AccountNotFoundError(
                    entry.meta, 'Account "{}" is not found or inactive, as well as all its sub-accounts'.format(account), entry
                ))
        else:
            accounts = [account] if account in self.open_accounts else []
            if not accounts:
                self.error(AccountNotFoundError(
                    entry.meta, 'Account "{}" is not found or inactive'.format(account), entry
                ))
        return accounts

    def process_close(self, entry: Close):
        self.open_accounts.remove(entry.account)
        self.entries.append(entry)

    def process_transaction(self, transaction: Transaction):
        # Extract the policy of transaction, if present
        transaction_policy = self.extract_policy(transaction.meta, transaction, required=False)
        # Split postings proportionately by parties
        postings_by_party = defaultdict(list)
        for posting in transaction.postings:
            policy = self.get_posting_policy(posting, transaction, transaction_policy)
            for party, share in policy.items():
                if share:
                    split_posting = utils.posting_distrib(posting, share, policy.total_weight)
                    split_posting = utils.strip_meta(split_posting)
                    postings_by_party[party].append(split_posting)
        # Create rounding postings for each party and add up all postings into real accounts
        residual_postings = []
        for party, party_postings in postings_by_party.items():
            residual = interpolate.compute_residual(party_postings)
            residual_postings += utils.get_residual_postings(residual, 'Assets:Receivable:{}'.format(party), negate=False)
            party_postings += utils.get_residual_postings(residual, 'Liabilities:Payable', negate=True)
            for posting in party_postings:
                # Use square brackets in account name to avoid collision with actual accounts
                real_account = realization.get_or_create(self.real_root, '{}:[{}]'.format(posting.account, party))
                real_account.balance.add_position(posting)
        # Finalize processed postings
        if self.viewpoint is None:
            postings = [utils.strip_meta(posting) for posting in transaction.postings]
            postings += residual_postings
        else:
            postings = postings_by_party.get(self.viewpoint, [])
        if postings:
            transaction = transaction._replace(
                postings = postings,
            )
            transaction = utils.strip_meta(transaction)
            self.entries.append(transaction)
    
    def get_account_policy(self, account: str) -> Optional[Policy]:
        policy = self.account_policies.get((account, False))
        if policy:
            return policy
        for account in utils.ancestor_accounts(account):
            policy = self.account_policies.get((account, True), None)
            if policy:
                return policy

    def get_posting_policy(self, posting: Posting, transaction: Transaction, transaction_policy: Optional[Policy]) -> Policy:
        policy = self.extract_policy(posting.meta, transaction, required=False) \
            or self.get_account_policy(posting.account) \
            or transaction_policy \
            or self.named_policies.get('default', None)
        if not policy:
            self.error(NoApplicablePolicyError(
                posting.meta, 'No applicable share policy to account "{}"'.format(posting.account), transaction
            ))
            return Policy()
        return policy

    def error(self, error):
        self.errors.append(error)

    def extract_policy(self, meta: Dict, entry: Optional[Directive] = None, required: bool = True) -> Optional[Policy]:
        policy = Policy()
        total_weight = 0
        found = False
        for k, v in meta.items():
            if k.startswith('share-'):
                party_name = k[len('share-'):]
                if not party_name:
                    self.error(InvalidSharePolicyError(
                        meta, 'Expect a name to share with', entry
                    ))
                elif not isinstance(v, Decimal):
                    self.error(InvalidSharePolicyError(
                        meta, 'Expect a weight of share in decimal', entry
                    ))
                elif not party_name[0].isupper():
                    self.error(InvalidSharePolicyError(
                        meta, 'The name to share with must start with an uppercase letter', entry
                    ))
                else:
                    found = True
                    policy[party_name] = v
                    total_weight += v
        policy.total_weight = total_weight
        if 'share_policy' in meta:
            if found:
                self.error(InvalidSharePolicyError(
                    meta, 'Mixed use of "share_policy" and "share-" attributes', entry
                ))
            elif meta['share_policy'] not in self.named_policies:
                self.error(InvalidSharePolicyError(
                    meta, 'Share policy "{}" does not exist'.format(meta['share_policy']), entry
                ))
            else:
                found = True
                policy = self.named_policies[meta['share_policy']]
        if required and not found:
            self.error(InvalidSharePolicyError(
                meta, 'Expect definition of share policy', entry
            ))
        return policy if found or required else None
