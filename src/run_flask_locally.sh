
PORT=7000

echo "Running flask locally on port ${PORT} ;)"

flask --app index run --host=0.0.0.0 --port=${PORT}
