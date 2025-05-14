# MIT License
#
# Copyright (c) 2024 Logan Gilbert
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
A helper script to run the DSX-Connect FastAPI app (dsx_connect.app.dsx_connect_app) as a Uvicorn web application,
serving an API for scanning file paths and rendering verdicts.

The app provides a Swagger/Redoc UI at http://<host>:<port>/docs or can be accessed via any REST API client (e.g., Postman, cURL).
"""

import os
import sys
import pathlib
import uvicorn

# Add the distribution root (directory containing this script) to sys.path
dist_root = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(dist_root))

if __name__ == "__main__":
    uvicorn.run(
        "dsx_connect.app.dsx_connect_app:app",
        host="0.0.0.0",
        port=8586,
        reload=True,  # Set to False in production with multiple workers
        workers=1
    )