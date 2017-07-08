import uuid
import base64

def get_id():
    unique_id = uuid.uuid4()
    unique_id_str = str(unique_id)
    return unique_id_str[-12:]

def generate_id_pool(num_objects):
    id_pool = []

    while len(id_pool) <= num_objects:
        id_num = get_id()
        if id_num not in id_pool:
            id_pool.append(id_num)

    return id_pool
