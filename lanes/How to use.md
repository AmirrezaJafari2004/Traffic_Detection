## Lane Setup

Lane files are not included in this repository because lane coordinates depend on the exact input video.

Each video has its own camera angle, resolution, road position, and lane layout. Therefore, lane definitions created for one video will not work correctly for another video.

Before processing a new video with lane-based analysis, you must create a lane definition file using:

```bash
python select_lanes.py
