clean:
ifeq ($(OS),Windows_NT)
	del *.log
else
	rm -f *.log
endif