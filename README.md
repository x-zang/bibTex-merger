# BibTeX File Merger
A Python script for merging multiple BibTeX `.bib` files, resolve conflicts, and removes duplicates.

## Usage

```bash
python bib-merger.py [options] input1.bib input2.bib [input3.bib ...] output.bib
```

### Arguments

- `input1.bib`, `input2.bib`, etc.: Input BibTeX files to merge
- `output.bib`: Output file for merged entries
- `--no-interactive`: (Optional) Run in non-interactive mode, automatically choosing entries when conflicts occur
- `--overwrite`: (Optional) Overwrite the output file without asking for confirmation

### Examples

```bash
# Interactive mode (default)
python bib-merger.py file1.bib file2.bib output.bib

# Non-interactive mode
python bib-merger.py --no-interactive file1.bib file2.bib output.bib
```

## How It Works

1. Consistency checks:
   - Articles with the same title & type should have the same key
   - Articles with the same key should have the same title & type
   - Note: conference/ journal/ preprint article with the same title are considered different articles
2. In interactive mode, it prompts the user to resolve conflicts
3. In non-interactive mode, it automatically chooses entries based on their first appearance

- e) or automatic selection (non-interactive mode)

## Known Issues

- If the title field contains comma (`,`), it might be truncated when parsing title. This parsed title field is only used for consistency checks. The final output is not affected.

## License

This project is open source and available under the MIT License. 