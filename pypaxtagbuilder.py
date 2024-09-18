from pycomm3 import LogixDriver
from sys import argv
import argparse
import xml.etree.ElementTree as ET
from itertools import product
import re
import xmlschema



def get_aoi_tag_instances(plc, tag_type):
    """
    function returns list of tag names matching struct type
    """
    #return tag_list

    tag_list = []

    for tag, _def in plc.tags.items():
        if _def['data_type_name'] == tag_type and not(_def['alias']):
            if _def['dim'] > 0:
                tag_list = tag_list + get_dim_list(tag,_def['dimensions'])
            else:
                tag_list.append(tag)

    return tag_list

def get_dim_list(base_tag, dim_list):
    '''
    function takes a list which has the array size and turns it into a list with all iterations
    '''
    # remove 0's
    filtered_list = list(filter(lambda num: num != 0, dim_list))

    temp = []

    for indices in product(*[range(dim) for dim in filtered_list]):
        temp.append(base_tag + ''.join(f'[{i}]' for i in indices))

    return temp

def write_tag(ET,parent,aoi_type,tag_name,param_list):
    '''
    Function adds a tag to the XML, assumes default parameters except plc name
    TO DO make it accept a dict of parameters
    '''

    tag = ET.SubElement(parent,"Tag", attrib={"name": str(tag_name),"type": str("UdtInstance")})
    tag.tail = '\n'

    prop = ET.SubElement(tag, "Property", attrib={"name": str("typeId")})
    prop.text = str(aoi_type)
    prop.tail = '\n'

    params = ET.SubElement(tag, "Parameters")
    params.tail = '\n'

    # Add parameters to the alarm
    for param_name in param_list.keys():
        param = ET.SubElement(params, "Property", attrib={"name":param_name,"type":"String"})
        param.text = param_list[param_name]
        param.tail = '\n'

def main():

    # will be replaced with PLC name
    default_AOI = 'P_AIn'

    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Python-based PlantPAX Ignition tag generator',
        epilog='This tool works on both Windows and Mac.')
    
    # Add command-line arguments
    parser.add_argument('commpath', help='Path to PLC')
    parser.add_argument('AOI', nargs='?', default=default_AOI,help='AOI to create tags for')
                                       
    args = parser.parse_args()

    # Access the parsed arguments
    commpath = args.commpath
    input_AOI = args.AOI

    # open connection to PLC

    plc = LogixDriver(commpath, init_tags=True,init_program_tags=True)

    print('Connecting to PLC.')
    try:
        plc.open()
        plc_name = plc.get_plc_name()

        print('Connected to ' + plc_name + ' PLC at ' + commpath)
    except:
        print('Unable to connect to PLC at ' + commpath)
        exit()

    print('Generating Ignition tag XML file')
    # create version element and append it to the root
    tags = ET.Element("Tags",attrib={
        "MinVersion": "8.0.0",
        "locale": "en_US"
    })

    # get list of tags for inputted AOI type
    aoi_instance_list = get_aoi_tag_instances(plc, input_AOI)

    if len(aoi_instance_list) > 0:

        for aoi_instance in aoi_instance_list:

            params = {"PLC": plc_name}
                
            write_tag(ET,tags,input_AOI,aoi_instance,params)


        print('Generation complete. Writing to file')
        # Create the XML tree
        tree = ET.ElementTree(tags)

        # add plc name to file and save to new file
        #outfile = appname + '_' + servername + '_AlarmExport.' + 'xml'
        outfile = plc_name + '_' + input_AOI + '_IgnitionTags.' + 'xml'
        # Write the XML tree to a file with UTF-16 encoding
        tree.write(outfile, encoding="utf-8", xml_declaration=False,short_empty_elements=False)
    else:
        print("No instances of type in PLC")


    plc.close()

if __name__ == "__main__":
    main()