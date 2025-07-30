import hashlib
def generate_checksum(request_data, key):
    """
    Generate SHA256 checksum required for PhonePe's X-VERIFY header.
    """
    checksum_string = f"{request_data}/pg/v1/pay{key}"
    return hashlib.sha256(checksum_string.encode()).hexdigest()