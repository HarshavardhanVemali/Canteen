import hashlib
def generate_checksum(data, salt_key, salt_index):
    """To Genarate checksum"""
    checksum_str = data + '/pg/v1/pay' + salt_key
    checksum = hashlib.sha256(checksum_str.encode()).hexdigest() + '###' + salt_index
    return checksum