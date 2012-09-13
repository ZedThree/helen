from enthought.traits.api import *
from enthought.traits.ui.api import *
from xml.etree.ElementTree import Element, SubElement, Comment, ElementTree
from xml.etree.ElementTree import XMLTreeBuilder
from ElementTree_pretty import prettify

import re
import copy

readinputfile='/home/peter/nemorb/peter/src/readinput.F90'
globalfile='/home/peter/nemorb/peter/src/globals.F90'

class InputXMLToNamelist(object):

    def __init__(self, outDict):
        self.outDict = outDict
        self.namelist_name = ''
        self.param_name = ''
        return

    def start(self, tag, attrib):
        if tag == 'namelist':
            # Make a new namelist object
            # 'name' attrib as key
            self.namelist_name = attrib['name']
            self.outDict[self.namelist_name] = Namelist()
        if tag == 'parameter':
            # Get the parameter name and type
            # We'll need them when the parameter tag is closed
            self.param_name = attrib['name']
            self.param_type = attrib['type']
        else:
            # Only other tags are default and description
            self.tag = tag
            
    def data(self, data):
        # For some reason, these tags get read 5 times, and all but once
        # are just whitespace/newlines!
        # So, strip all whitespace, and only use the one that isn't empty
        if self.tag == 'default':
            if data.strip() != '':
                if data.strip() == 'None':
                    self.param_default = None
            	else:
                    self.param_default = data.strip()
        elif self.tag == 'description':
            if data.strip() != '':
                self.param_desc = data.strip()

    def end(self, tag):
        if tag == 'parameter':
            # Actually create InputParam object when closing a parameter tag
            self.outDict[self.namelist_name][self.param_name] = InputParam(
                self.param_name,
                param_type = self.param_type,
                param_default = self.param_default,
                param_desc = self.param_desc)
    
    def close(self):
        # Nothing needs doing
        return
    

class InputParam(HasTraits):
    """ An input parameter """
    
    view = View(Item(name = 'value'),
                buttons = [OKButton, CancelButton])

    def __init__(self, param_name, param_type=None, param_default=None,
                 param_desc=None, species=None):
        if param_type is not None:
            self.type = param_type
        else:
            self.type = get_type(globalfile, param_name)
            
        if param_default is not None:
            self.default = param_default
        else:
            self.default = get_default(globalfile, param_name)
            # N.B. Need to implement a different get_default for parameters
            #      in 'attributes' namelist - also for electrons!

        if param_desc is not None:
            self.description = param_desc
        else:
            self.description = get_desc(readinputfile, param_name)
        # if species is not None:
        # This will be important later
        # This means we'll want to check readinputfile, not globalfile

        if self.type == 'float':
            real_param(self, name=param_name, default=self.default,
                       param_desc=self.description)
        if self.type == 'int':
            int_param(self, name=param_name, default=self.default,
                      param_desc=self.description)
        if self.type == 'str':
            str_param(self, name=param_name, default=self.default,
                      param_desc=self.description)
        if self.type == 'bool':
            bool_param(self, name=param_name, default=self.default,
                       param_desc=self.description)
            

class Namelist(dict):
    """ 
    A Fortran Namelist object.
    A dictionary of InputParam objects.
    """
    # This should hold specific values of input parameters,
    # either from having been read in, or from being created

    # Need to add an update method
    pass
    
    
class InputFile(dict):
    """ Input file object """
    

    def WriteInputFile(self):
        """ Writes the input file to disk """
        print """ writing file: \n
		nsel_equil = %i\n
		nptot      = %i """ % (
            self.nsel_equil, self.nptot )

    

def real_param(param_object, name, param_desc, default=None):
    """ Adds a Traits object for a Fortran real parameter """
    if default is None:
        default = 0.0
    else:
        default = float(default)
    param_object.default = default
    param_object.add_trait('value',Float(default,label=name,desc=param_desc))

def int_param(param_object, name, param_desc, default=None):
    """ A Traits object for a Fortran integer parameter """
    if default is None:
        default = 0
    else:
        default = int(default)
    param_object.default = default
    param_object.add_trait('value',CInt(default,label=name,desc=param_desc))

def str_param(param_object, name, param_desc, default=None):
    """ A Traits object for a Fortran character parameter """
    if default is None:
        default = ''
    else:
        default = str(default)
    param_object.default = default
    param_object.add_trait('value',String(default,label=name,desc=param_desc))

def bool_param(param_object, name, param_desc, default=None):
    """ A Traits object for a Fortran logical parameter """
    # A true value can have several forms in FORTRAN, so search for all of them
    # Assume anything else means FALSE
    grepTrue = re.compile(r"(true|t|1)",re.I)
    if grepTrue.search(str(default)):
        default = True
    else:
        default = False
    param_object.default = default
    param_object.add_trait('value',Bool(default,label=name,desc=param_desc))

def complex_param(param_object, name, param_desc, default=None):
    """ A Traits object for a Fortran complex parameter """
    if default is None:
        default = complex(0)
    else:
        default = complex(default)
    param_object.default = default
    param_object.add_trait('value',Complex(default,label=name,desc=param_desc))

def enum_param(param_object, name, param_desc, default=None):
    """ 
    A Traits object for a Fortran parameter which can only take certain values
    """
    if default is None:
        default = False
    param_object.default = default
    param_object.add_trait('value',Enum(default,label=name,desc=param_desc))

class scan_param(HasTraits):
    """ Choose which parameter to scan over """
   
    def __init__(self, namelist_in):
        paramlist = sorted(set(flatten(namelist_in)))
        self.add_trait('scan_param',Enum(paramlist,
                                        label="Parameter",
                                        desc="Input parameter to scan over",))


def pull_namelists(infile):
    """ Pull namelists out of file """
    
    # Read file
    with open(infile,'r') as f:
        f_content = f.read()
        # Collapse multilines
        f_content = re.sub("&[\s\t]*\n","",f_content)

        # Make regexp pattern
        nml_pattern = re.compile(r"NAMELIST[\s\t]*/(\w+)/[a-zA-Z0-9_,\s\t]*\n")
        # Find all the matches in the file for pattern, return as iterable object
        iterator = nml_pattern.finditer(f_content)
    
        # Make a namelist array
        nml = []
        # Populate the array with the matches from the file
        for match in iterator:
            tmp = match.group()
            nml.append(tmp)

            
    # Clean up namelist - remove multi-spaces, commas, and slashes
    nml = [re.sub("[\s\t]+"," ",item).strip() for item in nml]
    nml = [re.sub("[/,]"," ",item).strip() for item in nml]
    
    nml_dict = {}
    for item in nml:
        tmp = item.split()
        nml_dict[tmp[1]] = tmp[2:]
    
    return nml_dict
   

def get_type(infile, param):
    """ Determine a parameter's type by searching infile """
    
    # Pattern matching a definition line
    def_pattern = re.compile(r".*::[\s\ta-zA-Z_=0-9,+-]*"+param,re.I)
    # Patterns for different types
    float_pat = re.compile("REAL")
    int_pat = re.compile("INTEGER")
    str_pat = re.compile("CHARACTER")
    bool_pat = re.compile("LOGICAL")

    # Open the file, read it, then close
    f = open(infile,'r')
    f_content = f.read()
    f.close()

    # Search file for definition line
    def_line = def_pattern.search(f_content)
    if def_line:
        if float_pat.search(def_line.group()):
            param_type = 'float'
        elif int_pat.search(def_line.group()):
            param_type = 'int'
        elif str_pat.search(def_line.group()):
            param_type = 'str'
        elif bool_pat.search(def_line.group()):
            param_type = 'bool'
    else:
        param_type = 'err'
        
    return param_type

def get_desc(infile, param):
    """ Get the description of a parameter by searching infile """

    # There are descriptions of each parameter in globals.F90, where they are defined
    # There are better descriptions in readinput.F90, where they are stored!
    # A couple of records might be stupid...
    desc_pattern = re.compile(r"parameter.*\'" + param + "\',\'([^\']+)\'")
    desc_pattern2 = re.compile(r"creatd.*/" + param + "\',\'([a-zA-Z\s_]+)\'")

    # Open the file, read it, then close
    f = open(infile,'r')
    f_content = f.read()
    f.close()
    
    # Search file for store_parameter
    desc_line = desc_pattern.search(f_content)
    desc_line2 = desc_pattern2.search(f_content)
    param_desc = ''
    if desc_line:
        param_desc = desc_line.group(1)
    elif desc_line2:
        param_desc = desc_line2.group(1)

    return param_desc

def get_default(infile, param):
    """ Get the default value for a parameter, if one exists """
    
    # Pattern matching a definition line with initialisation
    default_pattern = re.compile(r".*::.*"+param+r" *= *([^,! ]*)")

    # Open the file, read it, then close
    f = open(infile,'r')
    f_content = f.read()
    f.close()

    # Search infile for default value
    default_line = default_pattern.search(f_content)
    if default_line:
        param_default = default_line.group(1)
    else:
        return None

    return param_default
    
def flatten(d):
    """Recursively flatten dictionary values in `d`.

    >>> hat = {'cat': ['images/cat-in-the-hat.png'],
    ...        'fish': {'colours': {'red': [0xFF0000], 'blue': [0x0000FF]},
    ...                 'numbers': {'one': [1], 'two': [2]}},
    ...        'food': {'eggs': {'green': [0x00FF00]},
    ...                 'ham': ['lean', 'medium', 'fat']}}
    >>> set_of_values = set(flatten(hat))
    >>> sorted(set_of_values)
    [1, 2, 255, 65280, 16711680, 'fat', 'images/cat-in-the-hat.png', 'lean', 'medium']
    """
    try:
        for v in d.itervalues():
            for nested_v in flatten(v):
                yield nested_v
    except AttributeError:
        for list_v in d:
            yield list_v

def generate_namelist_from_source():
    """
    This will generate a set of namelists from the source code.
    It should then write the namelist objects to file.
    """

    # The dictionary full of namelists and input parameters
    # Structure is {NAMELIST1: [var1 ... varN] ...}
    nml_dict = pull_namelists(readinputfile)
    
    # Now we want to create a second dictionary:
    # this one will be nested with the structure
    # {NAMELIST1: {var1: [InputParam object] ...} ...}
    # The InputParam objects for the generated namelists 
    # will contain the default values as traits.
    full_dict = {}
    for key in nml_dict.iterkeys():
        full_dict[key] = Namelist()
        for item in nml_dict[key]:
            full_dict[key][item] = InputParam(item)
        
    return full_dict


def read_generated_namelist(nml_file=None):
    """
    This will read a set of previously generated namelists from a file.
    """

    if not nml_file:
        # No file specified
        return None
    else:
        read_dict = {}
        target = InputXMLToNamelist(read_dict)
        parser = XMLTreeBuilder(target=target)
        with open(nml_file,'rt') as f:
            for line in f:
                parser.feed(line)
        parser.close()
        
    return read_dict

def write_generated_namelist(nml_file=None, nml_dict=None):
    """
    This will write a set of previously generated namelists to a file
    """
    
    if not nml_file:
        # No file specified
        return None
    elif not nml_dict:
        # No namelist specified
        return None
    else:
        top = Element('top')
        namelists = {}
        children = {}
        for key in nml_dict.keys():
            tmp = Element('namelist',name=key)
            for i in nml_dict[key]:
                children[i] = Element('parameter',
                                      name=i,
                                      type=nml_dict[key][i].type)
                default = SubElement(children[i],'default')
                default.text = str(nml_dict[key][i].default)
                desc = SubElement(children[i],'description')
                desc.text = nml_dict[key][i].description

            tmp.extend(children.values())
            top.append(tmp)
            children = {}

        # Open file
        with file(nml_file,'w') as f:
            f.write(prettify(top))
            
    return top

    # return fil


def read_inputfile():
    """
    This will read a set of namelists from an inputfile
    """
    # Structure of dictionary should be something like:
    # inputfile = {0:{'BASIC': ...}, ...}
    # with the different namelists being copy.deepcopy() of the namelist objects!
    # Then we can have multiple copies of the same namelist.
    


def write_inputfile():
    """
    This will write a set of namelists comprising an inputfile.
    """

if __name__ == "__main__":

# Ask user for number of species

# Make copies of all namelists into dictionary like
#{'0' : {'NUMBER_OF_SPECIES' : }
# '1' : {'BASIC' : }
# ...
# N : {'TYPE_SPECIES' : }}

# Ask user what parameters they want to scan over

# Write the input file


    pass
