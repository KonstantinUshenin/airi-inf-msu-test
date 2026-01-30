all:
	quarto render

clean:
	rm -rf _quarto
	rm -f slides.pdf slides.tex

