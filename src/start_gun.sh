
# Serve at port 7010

gunicorn -w 2 index:app -b 0.0.0.0:7010 &
