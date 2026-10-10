"""Shared presentation contract; rendering never establishes runtime authority."""
import hashlib
import json


def terminal_text(value):
    """Render untrusted data without terminal control sequences or Unicode width ambiguity."""
    text = str(value)
    return ''.join(c if 32 <= ord(c) <= 126 else c.encode('unicode_escape').decode('ascii') for c in text)


class KEDDEHHCIContract:
    def __init__(self, project_name, secure_context=True):
        self.project_name = project_name.upper()
        self.secure_context = secure_context
        self.active_state = 'IDLE'
        self.evidence_manifest = {}

    def render_iso_compliant_header(self, contextual_action_label):
        return '\n'.join(['=' * 69, ' SYSTEM ENGINE: ' + terminal_text(self.project_name),
                          ' CURRENT WORKING STATE: ' + terminal_text(self.active_state),
                          ' VIEW CONTEXT: ' + terminal_text(contextual_action_label), '-' * 69])

    def render_iso_compliant_footer(self, action_mapping):
        return '\n'.join(['-' * 69, ' AVAILABLE CONTROLS:',
                          ' | '.join(f'[{terminal_text(k)}] {terminal_text(v)}' for k, v in action_mapping.items()), '=' * 69])

    def commit_evidence_trace(self, input_action, processing_digest):
        """Local correlation digest only; not a signature or durable ledger receipt."""
        trace = hashlib.sha256(json.dumps([self.project_name, input_action, processing_digest],
                                         ensure_ascii=True, separators=(',', ':')).encode()).hexdigest()
        self.evidence_manifest[input_action] = 'LOCAL_TRACE:' + trace
        return self.evidence_manifest[input_action]

    def render(self, domain, observed_fields, actions):
        self.active_state = domain
        payload = json.dumps(observed_fields, sort_keys=True, ensure_ascii=True)
        trace = self.commit_evidence_trace('RENDER_SURFACE', hashlib.sha256(payload.encode()).hexdigest())
        return '\n'.join([self.render_iso_compliant_header(domain),
                          *(terminal_text(k) + ': ' + terminal_text(v) for k, v in observed_fields.items()),
                          trace, self.render_iso_compliant_footer(actions)])


class DomainSurface:
    domain = ''
    actions = {}

    def __init__(self, hci_core):
        self.hci = hci_core

    def execute_view_render(self, observed_fields):
        return self.hci.render(self.domain, observed_fields, self.actions)


class BRAINKSurface(DomainSurface):
    domain = 'BRAINK TELEMETRY'
    actions = {'A': 'Analyze stream', 'E': 'Emit proof', 'X': 'Disconnect'}


class KEXSurface(DomainSurface):
    domain = 'KEX RUNTIME'
    actions = {'S': 'Slot swap', 'W': 'Watchdog service', 'R': 'Reboot'}


class ILLLMSurface(DomainSurface):
    domain = 'IL-LLM MEANING ENGINE'
    actions = {'Q': 'Submit query', 'T': 'Tokenize input', 'P': 'Flush context'}


class CasePathSurface(DomainSurface):
    domain = 'CASEPATH EVIDENCE'
    actions = {'L': 'Lock case', 'U': 'Upload evidence', 'C': 'Audit ledger'}


class ClaimPathSurface(DomainSurface):
    domain = 'CLAIMPATH CONSENSUS'
    actions = {'V': 'Verify claim', 'S': 'Sign assertion', 'F': 'Reject claim'}


class FoundrySurface(DomainSurface):
    domain = 'FOUNDRY'
    actions = {'B': 'Build image', 'F': 'Flash storage', 'T': 'Self test'}


class ControlPlaneSurface(DomainSurface):
    domain = 'CONTROL PLANE'
    actions = {'G': 'Read mesh telemetry', 'A': 'Authorize node', 'K': 'Disconnect link'}
