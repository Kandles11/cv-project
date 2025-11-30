# notes

This folder contains experimental code for a slightly different approach to detecting tools.  The idea is to
- generate embeddings over all the tool images in our database using [DINOv2 image embedding model](https://github.com/facebookresearch/dinov2)
- store the embeddings in [DuckDB with `vss` extension](https://blog.brunk.io/posts/similarity-search-with-duckdb/) installed so we can do vector similarity search using HNSW indexes against our embedded DuckDB process
- Use a YOLO model (faster) or Grounding-DINO (probably better region results) or SAM2/MobileSAM to get regions in the incoming video frames which have a tool in them
    - This step isn't to classify the tool, just to identify that there is a tool in frame
- Generate vector embeddings over the proposed regions
- Calculate the similarity between the tool embeddings and the proposed regions to determine if the frame has a match against the tools in the tool embeddings in the database. 


Alternative idea that is slightly more rudimentary and more work:
Instead of using a model to get regions of interest in the video frames, divide the frame into overlapping regions. Then run GradCAM over every image. When GradCam results suggest that there is a tool in the region, run Segment Anything on the whole image to figure out the exact location of the tool in frame for tracking purposes. GradCAM (and other Pixel Attribution Methods) just estimate the likelihood that certain pixels in a region were likely to have tickled the embedding model in a certain way, producing a heat map of where the object in question is likely to be, but not actually giving you an actual bounding box or specific pixel regions - just giving you the blob of a region of interest. Using Segment Anything, we would have all the objects in the image segmented, so in combination with the GradCAM heatmaps, we could select the single object that is being tracked from the SAM output if there are multiple in frame.


