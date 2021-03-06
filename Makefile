PREFIX=/usr
DESTDIR=

INSTDIR=$(DESTDIR)$(PREFIX)
INSTBIN=$(INSTDIR)/local/bin

detected_OS := $(shell sh -c 'uname -s 2>/dev/null || echo not')
ifeq ($(detected_OS),Linux)
    INSTMAN=$(INSTDIR)/share/man/man7
endif
ifeq ($(detected_OS),Darwin)
    INSTMAN=$(INSTDIR)/local/share/man/man7
endif

SCRIPT=sc.py
MANPAGE=sc.7

all:
	@echo did nothing. try targets: install, or uninstall.

install:
	test -d $(INSTDIR) || mkdir -p $(INSTDIR)
	test -d $(INSTBIN) || mkdir -p $(INSTBIN)
	test -d $(INSTMAN) || mkdir -p $(INSTMAN)

	install -m 0755 $(SCRIPT) $(INSTBIN)/sc
	install -m 0644 doc/$(MANPAGE) $(INSTMAN)

uninstall:
	rm -f $(INSTBIN)/$(SCRIPT)
	rm -f $(INSTMAN)/$(MANPAGE)

link:
	ln -sf $(realpath $(SCRIPT)) $(INSTBIN)/sc

.PHONY: all install uninstall
