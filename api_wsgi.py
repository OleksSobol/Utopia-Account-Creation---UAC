from api_callback import UtopiaAPIHandler

utopia_handler = UtopiaAPIHandler()
app = utopia_handler.app

if __name__ == "__main__":
    utopia_handler.run()
