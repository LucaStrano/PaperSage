import hashlib
from PIL import Image
from typing import Any, List
from torch.functional import F


async def calculate_hash(content : bytes, buffer_size : int = 4096) -> str:
    """[ASYNC] Returns the truncated hash of the content using a buffer with `buffer_size` chunks."""
    hash_obj = hashlib.md5()
    for i in range(0, len(content), buffer_size):
        chunk = content[i:i+buffer_size]
        hash_obj.update(chunk)
    full_hash = hash_obj.hexdigest()
    truncated_hash = full_hash[:len(full_hash)//2]
    return truncated_hash

def embed_image(image : Image, img_model : Any, processor : Any, shortest_edge = 224) -> List[float]:
    """
    Embeds the image using the image model.
    Args:
        image (Image): Image object.
        img_model (Any): Image model loaded with AutoModel.
        processor (Any): Processor loaded with AutoImageProcessor.
        shortest_edge (int): Shortest edge parameter to pass to processor.
    Returns:
        List[float]: List of floats representing the image embedding.
    """
    # Process the image with the processor
    inputs = processor(image, return_tensors="pt", size={"shortest_edge": shortest_edge})
    img_emb = img_model(**inputs).last_hidden_state
    img_embeddings = F.normalize(img_emb[:, 0], p=2, dim=1)
    return img_embeddings[0].tolist()