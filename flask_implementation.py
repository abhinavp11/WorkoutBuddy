from website import create_app
app = create_app()



if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0")
#runs the app in DEBUG MODE so that it doesn't have to be run again every time it is updated