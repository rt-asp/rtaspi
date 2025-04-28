genexecutable:
	cp main.py rtaspi
	sed  -i '1i #!/usr/bin/python\n' rtaspi

install: genexecutable
	sudo cp rtaspi /usr/bin/
	sudo chmod +x /usr/bin/rtaspi
	rm rtaspi