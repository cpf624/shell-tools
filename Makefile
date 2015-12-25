INSTALL_PATH = /usr/local/bin

F1 = dopub(){ \
    f="$$1"; \
    if [ -d "$$f" ] && [ "$$f" != "./conf" ] && [ "$$f" != "./test" ] ;then \
        for sf in "$$f"/*; do \
            dopub "$$sf"; \
        done; \
    elif [ -f "$$f" ];then \
        cp "$$f" $(INSTALL_PATH); \
    fi;\
}

#修正conf目录文件权限
F2 = correct(){ \
    f="$$1"; \
    if [ -d "$$f" ];then \
        chmod 755 "$$f"; \
        for sf in "$$f"/*;do \
            correct "$$sf"; \
        done; \
    elif [ -f "$$f" ];then \
        chmod 644 "$$f"; \
    fi;\
}

.PHONY: install update

install:
	@$(F1); dopub .
	cp -rf conf $(INSTALL_PATH)
	cp docker/* $(INSTALL_PATH)
	rm $(INSTALL_PATH)/work $(INSTALL_PATH)/Makefile
	chmod 755 $(INSTALL_PATH)/*
	@$(F2); correct $(INSTALL_PATH)/conf
update:
	hg pull && hg update
