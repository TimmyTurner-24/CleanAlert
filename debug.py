from cleanalert import create_app

app_debug = create_app()

if __name__ == "__main__":
    app_debug.run(host='0.0.0.0', port=5001, debug=True)