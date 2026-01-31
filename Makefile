SHELL := /bin/bash

QMD := $(wildcard lectures/*.qmd)
PDF := $(patsubst lectures/%.qmd,pdf/%.pdf,$(QMD))

.PHONY: all clean render
all: $(PDF)

# Render one file -> produces one pdf
pdf/%.pdf: lectures/%.qmd
	@mkdir -p pdf
	quarto render $< --output-dir pdf

# Convenience: render everything (same as all)
render: all

clean:
	rm -rf _quarto .quarto pdf

