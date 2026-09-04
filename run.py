from cleanalert import create_app

# app = create_app()
app_debug = create_app()

if __name__ == "__main__":
    # app.run(host='0.0.0.0', port=5005, debug=False)
    app_debug.run(host='0.0.0.0', debug=True)