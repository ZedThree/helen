from enthought.traits.api import *
from enthought.traits.ui.api import *

import re

readinputfile='/home/peter/nemorb/peter/src/readinput.F90'
globalfile='/home/peter/nemorb/peter/src/globals.F90'

class input_param(HasTraits):
    """ An input parameter """

    def __init__(self, param_name, species=None):
        self.type = get_type(globalfile, param_name)
        self.default = get_default(globalfile, param_name)
        self.description = get_desc(readinputfile, param_name)
        # if species is not None:
        #     # This will be important later
        #     # This means we'll want to check readinputfile, not globalfile
        if self.type is 'float':
            self.value = real_param(name=param_name, default=self.default,
                                    desc_in=self.description)
        if self.type is 'int':
            self.value = int_param(name=param_name, default=self.default,
                                    desc_in=self.description)
        if self.type is 'str':
            self.value = str_param(name=param_name, default=self.default,
                                    desc_in=self.description)
        if self.type is 'bool':
            self.value = bool_param(name=param_name, default=self.default,
                                    desc_in=self.description)
            


# class namelist(dict):
#     """ A Fortran namelist """
    
#     def __init_(self):
        
    
    
class InputFile(dict):
    """ Input file object """
    

    def WriteInputFile(self):
        """ Writes the input file to disk """
        print """ writing file: \n
		nsel_equil = %i\n
		nptot      = %i """ % (
            self.nsel_equil, self.nptot )

    

class real_param(HasTraits):
    """ A Traits object for a Fortran real parameter """
   
    def __init__(self, name='Value', default=None, desc_in=''):
        HasTraits.__init__(self)
        if default is None:
            default = 0.0
        self.add_trait('value',Float(default,label=name,desc=desc_in))

class int_param(HasTraits):
    """ A Traits object for a Fortran integer parameter """
   
    def __init__(self, name='Value', default=None, desc_in=''):
        if default is None:
            default = 0
        self.add_trait('value',CInt(default,label=name,desc=desc_in))

class str_param(HasTraits):
    """ A Traits object for a Fortran character parameter """
   
    def __init__(self, name='Value', default=None, desc_in=''):
        if default is None:
            default = ''
        self.add_trait('value',String(default,label=name,desc=desc_in))

class bool_param(HasTraits):
    """ A Traits object for a Fortran logical parameter """
   
    def __init__(self, name='Value', default=None, desc_in=''):
        if default is None:
            default = False
        self.add_trait('value',Bool(default,label=name,desc=desc_in))

class all_params(HasTraits):
    """ All the possible input parameters """
   
    def __init__(self, inputlist=''):
        self.add_trait('obj',Enum(inputlist,
                                  label="Parameter",
                                  desc="Input parameter to scan over",))




def pull_namelists(infile):
    """ Pull namelists out of file """
    
    # Read file
    f = open(infile,'r').read()
    # Collapse multilines
    f = re.sub("&[\s\t]*\n","",f)

    # Make regexp pattern
    nml_pattern = re.compile(r"NAMELIST[\s\t]*/(\w+)/[a-zA-Z0-9_,\s\t]*\n")
    # Find all the matches in the file for pattern, return as iterable object
    iterator = nml_pattern.finditer(f)
    
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
    def_pattern = re.compile(r".*::[\s\ta-zA-Z_=0-9]*"+param)
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
    desc_pattern = re.compile(r"parameter.*\'" + param + "\',\'([a-zA-Z\s_]+)\'")
    desc_pattern2 = re.compile(r"creatd.*/" + param + "\',\'([a-zA-Z\s_]+)\'")

    # Open the file, read it, then close
    f = open(infile,'r')
    f_content = f.read()
    f.close()
    
    # Search file for store_parameter
    desc_line = desc_pattern.search(f_content)
    desc_line2 = desc_pattern2.search(f_content)
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
    

if __name__ == "__main__":
    inputfile = InputFile()
    inputfile.configure_traits()
    inputfile.WriteInputFile()
