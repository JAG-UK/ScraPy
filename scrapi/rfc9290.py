"""Encoder/Decoder for RFC9290 Concise Problem Details"""

import cbor2

DEFINED_FIELDS = {
    "title": -1,
    "detail": -2,
    "instance": -3,
    "response-code": -4,
    "base-uri": -5,
    "base-lang": -6,
    "base-rtl": -7,
}


def encode_problem_details(data):
    """
    Encodes a dictionary into a CBOR object according to RFC 9290 using numeric keys.

    Parameters:
        data (dict): Dictionary containing RFC 9290 problem details.

    Returns:
        bytes: CBOR-encoded bytes representing the problem details.
    """
    # Swap the dictionary keys to their numeric counterparts
    numeric_key_data = {
        DEFINED_FIELDS[k]: v for k, v in data.items() if k in DEFINED_FIELDS
    }
    return cbor2.dumps(numeric_key_data)


def decode_problem_details(cbor_data):
    """
    Decodes a CBOR-encoded problem details object with numeric keys into a dictionary.

    Parameters:
        cbor_data (bytes): CBOR-encoded bytes representing the problem details.

    Returns:
        dict: Dictionary containing RFC 9290 problem details with textual keys.
    """
    # Decode the CBOR data
    decoded_data = cbor2.loads(cbor_data)
    # Convert numeric keys back to their textual representation
    text_key_data = {
        key: decoded_data.get(DEFINED_FIELDS[key])
        for key in DEFINED_FIELDS
        if DEFINED_FIELDS[key] in decoded_data
    }
    return text_key_data
