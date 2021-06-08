import sys
sys.path.insert(0, '/home/ubuntu/DataArchitecture/')

from service import app

app.run(host="0.0.0.0", port=11100)
