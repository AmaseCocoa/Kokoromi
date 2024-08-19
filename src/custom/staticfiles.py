# Copyright (c) 2024 AmaseCocoa
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import os

import aiofiles
import brotli
import lightningcss
from fastapi import Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from rjsmin import jsmin


class StaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        request = Request(scope)
        file_path = os.path.join(self.directory, path)
        accept_encoding = request.headers.get('accept-encoding', '')

        if file_path.endswith('.js'):
            return await self.minify_and_compress(file_path, 'application/javascript', accept_encoding)
        elif file_path.endswith('.css'):
            return await self.minify_and_compress(file_path, 'text/css', accept_encoding)
        else:
            return await super().get_response(path, scope)

    async def minify_and_compress(self, file_path, media_type, accept_encoding):
        async with aiofiles.open(file_path, 'r', encoding="utf-8") as f:
            content = await f.read()
        
        if media_type == 'application/javascript':
            minified_content = jsmin(content)
        elif media_type == 'text/css':
            parser_flags = lightningcss.calc_parser_flags(nesting=True)
            minified_content = lightningcss.process_stylesheet(content, browsers_list=['defaults'])

        if 'br' in accept_encoding:
            compressed_content = brotli.compress(minified_content.encode('utf-8'))
            return Response(content=compressed_content, media_type=media_type, headers={"Content-Encoding": "br"})
        else:
            return Response(content=minified_content, media_type=media_type)