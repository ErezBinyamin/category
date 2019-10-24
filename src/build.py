"""Usage: build.py <input_dir> <output_dir> [rebuild]"""

import docopt, os, traceback, copy
from multiprocessing import Process, Queue
from . util import *
from . backends.xml.handler import xml_builder
from . backends.md.handler import md_builder
from . backends.md.plugins import *

NUM_WORKERS=20

def build_worker(inputs, outputs):
    for input_dir, output_dir, fn, extra_edges, md_time in iter(inputs.get, 'STOP'):
        ans = {'empty':True}
        try:
            ending = fn[fn.rfind('.'):]
            endings = {".md":md_builder, ".xml":xml_builder}
            if ending in endings:
                ans['empty'] = False
                common_prefix = os.path.commonprefix([input_dir, fn])
                src_path = os.path.relpath(fn, common_prefix)
                if os.path.getmtime(fn) < md_time:
                    ans['error'] = "Already up-to-date: {}".format(fn)
                    ans['empty'] = True
                else:
                    print("PROCESSING",fn)
                    args = {}
                    if ending == ".md":
                        args = {"plugins":{"slideshow":"md","math":{},"video":video.VideoPlugin(),"link":"txt","query":"txt","jsavr":"txt"}}
                    builder = endings[ending](fn,output_dir,**args)
                    if not builder.OK:
                        ans['error'] = "WARNING: There was a problem building {}".format(fn)
                    elif not 'name' in builder.node:
                        ans['error'] = "WARNING: No name found in {}".format(fn)
                    else:
                        if not 'edges' in builder.node:
                            builder.node['edges'] = {'has':{},'is':{}}
                        builder.node['src'] = src_path
                        edges = builder.node['edges']
                        add_edges(extra_edges, edges)
                        ans['error'] = None
                        ans['builder'] = builder
        except Exception as e:
            ans['error'] = f"Exception building: {fn}:\n" + traceback.format_exc()
            ans['empty'] = False
            
        outputs.put(ans)

class cat_builder:
    def __init__(self, input_dir, output_dir, force_rebuild=False):
        md_file = os.path.join(output_dir,'metadata.json')
        self.md_time = 0
        self.metadata = {}
        if os.path.isfile(md_file) and not force_rebuild:
            self.metadata = import_metadata(md_file)
            self.md_time = os.path.getmtime(md_file)

        input_queue = Queue()
        output_queue = Queue()
        num_inputs = 0
        by_src = {self.metadata[node_id]['src']:node_id for node_id in self.metadata if 'src' in self.metadata[node_id]}
        for x in by_src:
            if 'quest' in x:
                print(x)

        # The name of the metadata file that that will contain edges for all nodes in a subdirectory
        self.metadata_conf = "metadata.conf"

        # The current set of edges read from a config file
        self.config_edges = {}

        # Save off all the source paths so we can check if a file has been compiled already
        srcs = {x.get('src','') for x in self.metadata.values()}

        # If we're not rebuilding, iterate through the metadata
        # elements and remove those whose source files no longer exist
        if not force_rebuild:
            to_del = []

            # Look for removed nodes
            for node_id in self.metadata:
                if 'src' in self.metadata[node_id] and not os.path.exists(os.path.join(input_dir, self.metadata[node_id]['src'])):
                    to_del.append(node_id)
                    
            for node_id in to_del:
                del self.metadata[node_id]
        
        for dirname,dirs,files in os.walk(input_dir):
            # Skip the OLD directory
            if "OLD" in dirname:
                print("skipping OLD")
                continue
            
            # Read the metadata
            if self.metadata_conf in files:
                print("found config in",dirname)
                with open(os.path.join(dirname, self.metadata_conf),"r") as f:
                    _,self.config_edges = parse_config(f.read())
                    
            # Now read the actual data files
            for fn in files:
                fn = os.path.join(dirname, fn)
                input_queue.put([input_dir, output_dir, fn, copy.deepcopy(self.config_edges), self.md_time])
                num_inputs += 1

        # Now start the workers
        for i in range(NUM_WORKERS):
            Process(target=build_worker, args=(input_queue, output_queue)).start()

        for i in range(NUM_WORKERS):
            input_queue.put('STOP')

        errors = []
        
        # The results should come in output_queue
        for i in range(num_inputs):
            ans = output_queue.get()
            if ans['empty']: continue
            elif not ans['error'] is None:
                errors.append(ans['error'])
                continue
            builder = ans['builder']
            node_src_path = builder.node['src']
            print("SRC",node_src_path)
            
            # Ensure no ID collisions
            if builder.ID in self.metadata:
                es = "ERROR: Two nodes with the same name: {}\nSrc: {}\n"
                print(es.format(builder.node['name'], node_src_path))
                return

            # Check for name change
            if not force_rebuild:
                if by_src.get(node_src_path,None) != builder.ID:
                    es = "WARNING: Node changed name: {} -> {}\n"
                    print(es.format(self.metadata[by_src[node_src_path]]['name'], builder.node['name']))
                    del self.metadata[by_src[node_src_path]]

            # Get the path of the file to write the processed document to
            output_path = os.path.join(output_dir,'{}.html'.format(builder.ID))
            print("WRITING {}: {} -> {}".format(builder.node['name'], builder.node['src'], output_path))

            # Add the data to our metadata dictionary
            self.metadata[builder.ID] = builder.node

            # Actually write the output document
            with open(output_path,"wb") as f:
                f.write(builder.doc)

        print("completing metadata")
        self.metadata = complete_metadata(self.metadata)
        print("metadata complete")
        # for x in self.metadata:
        #     print("MD",x,self.metadata[x])
        with open(os.path.join(output_dir,'metadata.json'),"w") as f:
            f.write(jsonenc().encode(self.metadata))

        print("metadata written")
            
        if len(errors) > 0:
            print("ERRORS: ", "\n-----\n".join(errors))
        
if __name__ == "__main__":
    args = docopt.docopt(__doc__)
    cat_builder(args['<input_dir>'], args['<output_dir>'],args['rebuild'])
