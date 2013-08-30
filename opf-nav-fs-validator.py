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
regex_misc_file = '^.*\.x?html?$' # negate! # TODO: Lower-/Uppercase
regex_no_external_images = '^http://.*$' # negate!

# =================================

def convert_to_relpaths(filelist):
    for i, filename in enumerate(filelist):
        filelist[i] = path.relpath(filename)
    return filelist

# =================================

# get opfs mapped in container.xml
def getmapped_opfs():
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
    if (len(fs_htmls) < 1):
        err('ERROR: No HTMLs found in filesystem. This should not happen!')
        sys.exit(1)
    return convert_to_relpaths(fs_htmls)

# =================================

def getmapped_navs():
    nav_htmls = []
    for opf in getmapped_opfs():
        if not(path.isfile(opf)):
            warn('WARNING: OPF file {0} not found. It will be ignored.'.format(opf))
            continue
        found_navs = lxml.etree.parse(opf).xpath("//o:item[@properties = 'nav']/@href", namespaces={'o': 'http://www.idpf.org/2007/opf'})
        if len(found_navs) < 1:
            err('ERROR: No nav found in OPF: ' + opf)
            sys.exit(1)            
        elif len(found_navs) > 1:
            err('ERROR: More than one nav found in OPF: ' + opf)
            sys.exit(1)
        nav_htmls.append(path.join(path.dirname(opf), found_navs[0]))
    return convert_to_relpaths(nav_htmls)

# =================================

# get all htmls which are mapped by nav file
def getmapped_htmls():
    nav_files = []
    for nav in getmapped_navs():
        found_files = lxml.html.parse(nav).xpath('//a/@href')
        if (len(found_files) < 1):
            err('ERROR: No referenced files found in: ' + nav)
            sys.exit(1)
        for found_file in found_files:
            found_file = path.relpath(path.join(path.dirname(nav), found_file))
            nav_files.append([found_file, nav])
    return nav_files # TODO: NAV and OPF file in third array place and convert_to_relpaths 

# =================================

# gets all OPFs from container and returns all [href, OPF_filename] which matches a regex pattern
def _getmapped_opf_regex_files(regex, negate=False):
    opf_files = []
    for opf in getmapped_opfs():
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

def getmapped_opf_misc():
    return _getmapped_opf_regex_files(regex_misc_file, negate=True)

# =================================

# gets all files from html in NAVs from opfs and returns all [img @src, nav_filename, opf_filename] which matches a regex pattern.
# regex is not really needed because we only support images at the moment
def _getmapped_html_regex_files(regex, negate=False):
    img_files = []
    for html, nav in getmapped_htmls():
        found_files = lxml.html.parse(html).xpath('//img/@src')
        for found_file in found_files:
            if ((re.match(regex, found_file) and not(negate)) \
            or (not(re.match(regex, found_file)) and negate)):
                found_file = path.relpath(path.join(path.dirname(html), found_file))
                img_files.append([found_file, html])
    return img_files # TODO: OPF file in third array place and convert_to_relpaths

def getmapped_html_images():
    return _getmapped_html_regex_files(regex_no_external_images, negate=True)

def main():
    infog('Analyzing OPFs...')
    opf_fs = set(getfs_opfs())
    opf_mapped = set(getmapped_opfs())
    info('=== OPF files missing on filesystem:')
    for missing in opf_mapped.difference(opf_fs):
        print(missing)
    info('=== OPF files not mapped in container.xml:')
    for missing in opf_fs.difference(opf_mapped):
        print(missing)

    infog('Analyzing NAVs...')
    nav_fs = set(getfs_navs())
    nav_mapped = set(getmapped_navs())
    info('=== NAV files missing on filesystem:')
    for missing in nav_mapped.difference(nav_fs):
        if not(path.isfile(missing)):
            print(missing)
    info('=== NAV files not mapped OPF:')
    for missing in nav_fs.difference(nav_mapped):
        print(missing)

    infog('Analyzing HTMLs....')
    html_fs = set(getfs_htmls())
    html_mapped_one_dimension = []
    for a, b in getmapped_htmls():
        html_mapped_one_dimension.append(a)
    html_mapped = set(html_mapped_one_dimension).intersect(getmapped_navs())
    info('=== HTML files missing on filesystem:')
    for missing in html_mapped.difference(html_fs):
        if not(path.isfile(missing)):
            print(missing)
    info('=== HTML files not mapped in NAV (please ignore navs itself!):')
    for missing in html_fs.difference(html_mapped):
        print(missing)

    infog('Analyzing image/external files....')
    images_mapped_one_dimension = []
    for a, b in getmapped_html_images():
        images_mapped_one_dimension.append(a)
    imaged_mapped = set(images_mapped_one_dimension)
    info('=== image files missing on filesystem:')


# =================================

if  __name__ == '__main__':
    main()
