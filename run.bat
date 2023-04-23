powershell "Copy-item -path .\Backend.py -destination .\Conf\py\Lib\site-packages\Backend.py"
powershell "./Conf/py/python.exe frontend.py"