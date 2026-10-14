"""Shared model visibility for durable rows retained in the human transcript."""


def is_model_visible(message):
    metadata = message.get("display_metadata") or {}
    return not (isinstance(metadata, dict) and metadata.get("human_only") is True)


def model_visible_messages(messages):
    if all(is_model_visible(message) for message in messages):
        return messages
    return [message for message in messages if is_model_visible(message)]
