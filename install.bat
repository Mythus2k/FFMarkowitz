powershell -c "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.10.11/python-3.10.11-embed-amd64.zip' -OutFile '.\Conf\temp.zip'"
powershell "Expand-Archive -Force '.\Conf\temp.zip' '.\Conf\py\'"
powershell "Remove-Item '.\Conf\temp.zip'"

powershell "Remove-Item './Conf/py/python310._pth'"
powershell "Copy-Item -Path ./Conf/py_setup/python310._pth -Destination ./Conf/py/python310._pth"

powershell "./Conf/py/python.exe ./Conf/py_setup/get_pip.py"

powershell "./Conf/py/python.exe -m pip install yfinance"
powershell "./Conf/py/python.exe -m pip install matplotlib"
powershell "./Conf/py/python.exe -m pip install numpy"
powershell "./Conf/py/python.exe -m pip install pandas"
powershell "./Conf/py/python.exe -m pip install scikit-learn"
powershell "./Conf/py/python.exe -m pip install scipy"
powershell "./Conf/py/python.exe -m pip install dearpygui"
powershell "Copy-item -path .\Backend.py -destination .\Conf\py\Lib\site-packages\Backend.py"