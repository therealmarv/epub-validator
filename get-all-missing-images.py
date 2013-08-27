import fnmatch
import os
import lxml.html

# Get all missing images on FS from nav's htmls

# =================================
# just some fancy colors for output

HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = "\033[1m"

def disable():
    HEADER = ''
    OKBLUE = ''
    OKGREEN = ''
    WARNING = ''
    FAIL = ''
    ENDC = ''

def infog(msg):
    print OKGREEN + msg + ENDC

def info(msg):
    print OKBLUE + msg + ENDC

def warn(msg):
    print WARNING + msg + ENDC

def err(msg):
    print FAIL + 'ERROR: ' + msg + ENDC

# =================================

def main():
    # nav_matches contains all found *nav*html files. Useful later for checking against opf files
    nav_matches = []
    for root, dirnames, filenames in os.walk('.'):
      for filename in fnmatch.filter(filenames, '*nav*html'):
          nav_matches.append(os.path.join(root, filename))

    # Check if all files in nav files exist and check if images exist
    for nav_file in nav_matches:
        print '====== Analysing navigation HTML: ' + nav_file
        nav_htmls = lxml.html.parse(nav_file).xpath("//a/@href")
        for nav_html in nav_htmls:
            nav_html = os.path.join(os.path.dirname(nav_file), nav_html)
            if not(os.path.isfile(nav_html)):
                err('HTML file {0} in {1} does not exist!'.format(nav_html, os.path.basename(nav_file)))
                continue
            #print '----- Analysing: ' + nav_html
            img_links = lxml.html.parse(nav_html).xpath("//img/@src")
            for img_link in img_links:
                img_file = os.path.join(os.path.dirname(nav_html), img_link)
                if not(os.path.isfile(img_file)):
                    err('Image file {0} in {1} does not exist!'.format(img_file, nav_html))
                    continue

# =================================

if  __name__ == '__main__':
    main()
