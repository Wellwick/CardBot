class OptionNode:
    def __init__(self, text):
        self.text = text
        self.next = None

    def is_option(self):
        return True

class StoryNode:
    def __init__(self, text):
        self.text = text
        self.next = None
        self.options = []

    def add_option(self, option):
        self.options += [ option ]

    def is_option(self):
        return False

    def is_end(self):
        return self.next == None and len(options) == 0


class Story:
    def __init__(self, name):
        self.name = name
        self.current_node = start_node


    def load_story(self, inputs):
        """
        Inputs come in the format for an n by 3 array, where the first
        column is either STORY or OPTION, the second is always text
        and the third is either a number, empty or END, signifying the end
        of the story. The value of 3rd column will always be +2 of the index,
        so make sure to offset by this!
        """
        offset = -2
        nodes = []
        # You do not have to start with STORY
        for i in inputs:
            if i[0] == "":
                break
            elif i[0] == "OPTION":
                if len(nodes) == 0:
                    # We're starting on an option
                    nodes += [ StoryNode("Pick an option to start:") ]
                    offset += 1
                nodes += [ Option(i[1]) ]
            elif i[0] == "STORY":
                nodes += [ StoryNode(i[1]) ]
            else:
                self.current_node = StoryNode("Could not load story")
                return

        # Now that we've created all the nodes so we can point at them, 
        # let's create the sequence
        lastNode = nodes[0]
        for i in range(1, len(nodes)):
            input_index = i - 2 - offset
            if nodes[i].is_option():
                # Option nodes should not point to anything
                if lastNode.next == None:
                    lastNode.next = None
                lastNode.add_option(nodes[i])
                val = inputs[input_index][2]
                nodes[i].next = nodes[int(val)+offset]
            else:
                if inputs[input_index][2] != "END":
                    nodes[i].next = nodes[i+1]







