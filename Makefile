# Arffornia docs — `make check` is what CI runs.
SYSTEM  := architecture/arffornia
VIEWS   := $(basename $(notdir $(wildcard $(SYSTEM)/views/*.yaml)))
OUT     := docs/assets/diagrams
INFRA   ?= ../infra
DRAWIO  ?= drawio
ICONS   := -icons .noodle/icons

.PHONY: check build serve lint-diagrams diagrams discover test-scripts stack clean

check: test-scripts lint-diagrams build

test-scripts:     ## offline tests of the board and chantier scripts (Python 3.9+, stdlib)
	PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts -p 'test_*.py'

stack:            ## print Brian's stack of chantiers (REST; GH_TOKEN or the gh CLI)
	python3 -B scripts/chantiers.py

build:            ## build the site, failing on broken links or warnings
	mkdocs build --strict

serve:            ## live preview on http://127.0.0.1:8000
	mkdocs serve

lint-diagrams:    ## Noodle check + lint of every view
	@for v in $(VIEWS); do echo "noodle: $$v"; noodle render $(SYSTEM) -view $$v $(ICONS) || exit 1; done

diagrams:         ## render every view, both themes, PNG + editable SVG (needs draw.io; PNG scale capped at ~3900 px, wider exports get cropped headless)
	@mkdir -p $(OUT)
	@for v in $(VIEWS); do for t in dark light; do \
	  noodle render $(SYSTEM) -view $$v $(ICONS) -theme $$t -o $(OUT)/$$v.$$t.drawio && \
	  W=$$(grep -o 'pageWidth="[0-9]*"' $(OUT)/$$v.$$t.drawio | head -1 | tr -dc 0-9) && \
	  S=$$(awk -v w=$$W 'BEGIN{s=3900/(w+40); if(s>2)s=2; printf "%.2f", s}') && \
	  $(DRAWIO) -x -f png -s $$S --border 20 -o $(OUT)/$$v.$$t.png $(OUT)/$$v.$$t.drawio && \
	  $(DRAWIO) -x -f svg --embed-diagram -o $(OUT)/$$v.$$t.drawio.svg $(OUT)/$$v.$$t.drawio || exit 1; \
	done; done

discover:         ## refresh Kubernetes facts from the infra repo (INFRA=path)
	./scripts/discover.sh $(INFRA) $(SYSTEM)/discovered

clean:
	rm -rf site
