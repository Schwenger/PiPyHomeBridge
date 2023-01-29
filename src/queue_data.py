"Data to be put into the queue."

from remote import Remote

KIND_REFRESH = "Refresh"
KIND_REMOTE_MESSAGE = "Remote Message"

REFRESH = { "kind" : KIND_REFRESH }
def remote_message(remote: Remote, action: str):
    "A message from a remote was received"
    return {
        "kind": KIND_REMOTE_MESSAGE,
        "remote": remote,
        "action": action,
    }
