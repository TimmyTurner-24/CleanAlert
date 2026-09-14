from cleanalert import create_app

app = create_app()
# Preserve compatibility with the previous WSGI entry point.
app_debug = app

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False)
