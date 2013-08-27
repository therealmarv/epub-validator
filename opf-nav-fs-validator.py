import fnmatch
import os
from os import path
import sys
import re
import lxml.html
import lxml.etree


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

startpath = '.'
regex_html_file = '^.*\.x?html?$' # TODO: Lower-/Uppercase
regex_image_file = '^.*\.(jpg|jpeg|gif|png)$' # TODO: Lower-/Uppercase
regex_misc_file = '^.*(\.(x?html?|jpg|jpeg|gif|png))$' # negate # TODO: Lower-/Uppercase

# =================================

def convert_to_relpaths(filelist):
    for i, filename in enumerate(filelist):
        filelist[i] = path.relpath(filename)
    return filelist

# =================================

def getcontainer_opfs():
    container_file = path.join(startpath, 'META-INF', 'container.xml')
    if not(path.isfile(container_file)):
        err('ERROR: META-INF/container.xml was not found! Not valid EPUB!')
        sys.exit(1)
    meta_opfs = lxml.etree.parse(container_file).xpath('//o:rootfile/@full-path', namespaces={'o': 'urn:oasis:names:tc:opendocument:xmlns:container'})
    if (len(meta_opfs) < 1):
        err('ERROR: META-INF/container.xml has no OPFs inside. This should not happen!')
        sys.exit(1)
    return convert_to_relpaths(meta_opfs)

# =================================

def getfs_opfs():
    fs_opfs = []
    for root, dirnames, filenames in os.walk('.'):
      for filename in fnmatch.filter(filenames, '*.opf'):
          fs_opfs.append(os.path.join(root, filename))
    if (len(fs_opfs) < 1):
        err('ERROR: No OPFs found in filesystem. This should not happen!')
        sys.exit(1)
    return convert_to_relpaths(fs_opfs)

# =================================

def getfs_navs():
    fs_navs = []
    for root, dirnames, filenames in os.walk('.'):
      for filename in fnmatch.filter(filenames, '*nav*html'):
          fs_navs.append(os.path.join(root, filename))
    if (len(fs_navs) < 1):
        err('ERROR: No NAVs found in filesystem. This should not happen!')
        sys.exit(1)
    return convert_to_relpaths(fs_navs)

# =================================

def getfs_htmls():
    fs_htmls = []
    for root, dirnames, filenames in os.walk('.'):
      for filename in fnmatch.filter(filenames, '*html'):
          fs_htmls.append(os.path.join(root, filename))
    if (len(fs_navs) < 1):
        err('ERROR: No HTMLs found in filesystem. This should not happen!')
        sys.exit(1)
    return convert_to_relpaths(fs_navs)

# =================================

def getmapped_navs():
    nav_htmls = []
    for opf in getcontainer_opfs():
        found_navs = lxml.etree.parse(opf).xpath("//o:item[@properties = 'nav']/@href", namespaces={'o': 'http://www.idpf.org/2007/opf'})
        if len(found_navs) < 1:
            err('ERROR: No nav found in OPF: ' + opf)
            sys.exit(1)            
        elif len(found_navs) > 1:
            err('ERROR: More than one nav found in OPF: ' + opf)
            sys.exit(1)
        nav_htmls.append(found_navs[0])
    return convert_to_relpaths(nav_htmls)

# =================================

# gets all OPFs from container and returns all [href, OPF_filename] which matches a regex pattern
def _getmapped_opf_regex_files(regex, negate=False):
    opf_files = []
    for opf in getcontainer_opfs():
        opf = path.relpath(opf)
        found_files = lxml.etree.parse(opf).xpath("//o:item[not(@properties = 'nav')]/@href", namespaces={'o': 'http://www.idpf.org/2007/opf'})
        if len(found_files) < 1:
            err('ERROR: No referenced files found in: ' + opf)
            sys.exit(1)
        for found_file in found_files:
            if ((re.match(regex, found_file) and not(negate)) \
            or (not(re.match(regex, found_file)) and negate)):
                found_file = path.relpath(path.join(path.dirname(opf), found_file))
                opf_files.append([found_file, opf])
    return opf_files # convert_to_relpaths(opf_files) # TODO for two arrays

# =================================

def getmapped_opf_htmls():
    return _getmapped_opf_regex_files(regex_html_file)

# =================================

def getmapped_opf_images():
    return _getmapped_opf_regex_files(regex_image_file)

# =================================

def getmapped_opf_misc():
    return _getmapped_opf_regex_files(regex_misc_file)

# =================================

#TODO

# gets all OPFs from container
# negate is needed because you cannot negative regex :(
# returns all [href, OPF_filename] which matches a regex pattern
def _getmapped_opf_regex_files(regex, negate=False):
    opf_files = []
    for opf in getcontainer_opfs():
        opf = path.relpath(opf)
        found_files = lxml.etree.parse(opf).xpath("//o:item[not(@properties = 'nav')]/@href", namespaces={'o': 'http://www.idpf.org/2007/opf'})
        if len(found_files) < 1:
            err('ERROR: No referenced files found in: ' + opf)
            sys.exit(1)
        for found_file in found_files:
            if ((re.match(regex, found_file) and not(negate)) \
            or (not(re.match(regex, found_file)) and negate)):
                found_file = path.relpath(path.join(path.dirname(opf), found_file))
                opf_files.append([found_file, opf])
    return opf_files # convert_to_relpaths(opf_files) # TODO for two arrays

# =================================

def main():
    # print getmapped_opf_images()
    print getmapped_opf_images()

# =================================

def oldmain():
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
