from app import App
from lib.nn import NN
from ui.gui import UI
import sys



def main(args):
	if len(args)==1:
		args.append("-gui")
	app = App()

	if args[1] == "-noGui":
		app.runAll()
	else:
		ApplicationUI = UI(app)


if __name__ == "__main__":
   main(sys.argv)