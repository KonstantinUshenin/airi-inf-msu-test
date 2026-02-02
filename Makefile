SHELL := /bin/bash

QMD := $(wildcard lectures/*.qmd)
PDF := $(patsubst lectures/%.qmd,pdf/%.pdf,$(QMD))

DOT := $(wildcard lectures/plots/*.dot)
PNG := $(DOT:.dot=.png)

.PHONY: all pdf dot clean

# Top-level target
all: pdf

# Phase 2: PDFs (depends on plots)
pdf: dot $(PDF)

# Phase 1: Graphviz
dot: $(PNG)

# ---- Rules -------------------------------------------------

pdf/%.pdf: lectures/%.qmd
	@mkdir -p pdf
	quarto render $< --output-dir pdf

lectures/plots/%.png: lectures/plots/%.dot
	dot -Tpng $< -o $@

clean:
	rm -rf _quarto .quarto pdf
	rm -f lectures/plots/*.png
