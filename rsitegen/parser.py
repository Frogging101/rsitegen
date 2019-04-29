import markdown

def consume_headers(f):
    headers = dict()

    for line in f:
        if not line or line.isspace():
            break
        split = line.partition(':')
        if split[0] and split[2]:
            headers[split[0]] = split[2]
        else:
            break

    return headers

def parse_markdown(path):
    class Page: pass
    page = Page()

    md = markdown.Markdown(extensions=["meta"])
    with open(path, 'r') as f:
        #metadata = consume_headers(f)
        #for k,v in metadata.items():
        #    setattr(page, k, v)
        html = md.convert(f.read())

    for k,v in md.Meta:
        setattr(page, k.lower(), v)

    page.content = html
    return page
