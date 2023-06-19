clean:
ifeq ($(OS),Windows_NT)
	del /q *.log
	make clean -C user_logger
else
	rm -f *.log
	make clean -C user_logger
endif