# Third-Party Notices

This project depends on third-party open-source software. The main upstream
dependencies are Microsoft MarkItDown, pdfplumber, and Docling.

## Microsoft MarkItDown

- Project: https://github.com/microsoft/markitdown
- Package: `markitdown`
- License: MIT License
- Copyright: Copyright (c) Microsoft Corporation.

MarkItDown Desktop is an unofficial desktop wrapper. It is not affiliated with,
endorsed by, sponsored by, or maintained by Microsoft.

When MarkItDown is installed or bundled with this application, its MIT License
notice must be preserved:

```text
MIT License

Copyright (c) Microsoft Corporation.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE
```

## pdfplumber

- Project: https://github.com/jsvine/pdfplumber
- Package: `pdfplumber`
- License: MIT License
- Copyright: Copyright (c) 2015, Jeremy Singer-Vine
- Purpose: Auto PDF layout repair fallback

pdfplumber is a third-party project. When pdfplumber is installed or bundled
with this application, its MIT License notice must be preserved:

```text
The MIT License (MIT)

Copyright (c) 2015, Jeremy Singer-Vine

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Docling

- Project: https://github.com/docling-project/docling
- Package: `docling`
- License: MIT License
- Copyright: Copyright (c) 2024 International Business Machines
- Purpose: Auto PDF fallback and optional Docling conversion mode

Docling is a third-party project. When Docling is installed or bundled with this
application, its MIT License notice must be preserved:

```text
MIT License

Copyright (c) 2024 International Business Machines

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

Individual bundled models and transitive dependencies may have their own
licenses and should be reviewed when preparing formal releases.

## Other Dependencies

This app uses Python's standard-library Tkinter toolkit for the desktop UI.
It also depends on the optional dependencies installed by `markitdown[all]`.
Their licenses are distributed by their package metadata and should be reviewed
when preparing formal releases.
