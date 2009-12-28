import sys, re, math

# warning: does not support continuous features

class Feature:
    def __init__(self, alpha, column, value=None):
        self.alpha = alpha
        self.column = column
        self.value = value
        self.threshold = None
        self.c0 = []
        self.c1 = []
        self.c2 = []

class Classifier:
    def __init__(self, stem=None):
        self.features = []
        self.names = {}
        self.classes = []
        if stem:
            self.load_model(stem)

    def load_model(self, stem):
        self.read_names(stem + ".names")
        self.read_shyp(stem + ".shyp")

    def read_names(self, names_file):
        classes = None
        columns = []
        for line in open(names_file).xreadlines():
            line = line.strip()
            if classes == None:
                classes = [x.strip() for x in re.sub('\.$', '', line).split(',')]
                self.classes = classes
            else:
                name = re.split(r':', line)[0]
                self.names[name] = len(self.names)
    
    def read_shyp(self, shyp_file):
        num_classifiers = None
        feature = None
        line_num = 0
        for line in open(shyp_file).xreadlines():
            line_num += 1
            line = line.strip()
            if line == "":
                continue
            tokens = line.split()
            found_sgram = re.search(r'^\s*(\S+)\s+Text:SGRAM:([^:]+):(.*?) *$', line)
            if num_classifiers == None:
                num_classifiers = int(line)
            elif found_sgram:
                alpha = float(found_sgram.group(1))
                column = found_sgram.group(2)
                value = found_sgram.group(3)
                feature = Feature(alpha, column, value)
                self.features.append(feature)
            elif feature != None and len(tokens) == len(self.classes):
                if feature.c0 == []: feature.c0 = [float(x) * feature.alpha for x in tokens]
                elif feature.c1 == []: feature.c1 = [float(x) * feature.alpha for x in tokens]
                elif feature.c2 == []: feature.c2 = [float(x) * feature.alpha for x in tokens]
                else:
                    sys.stderr.write('ERROR: too many weights, in %s, line %d\n' % (shyp_file, line_num))
                    return None
            else:
                sys.stderr.write('ERROR: unsupported classifier, in %s, line %d\n' % (shyp_file, line_num))
                return None

    # example should be [set(), set(), ...] with a set for each column
    def compute_scores(self, example):
        scores = [0.0 for x in self.classes]
        for feature in self.features:
            if feature.value in example[self.names[feature.column]]:
                for i in range(len(feature.c1)):
                    scores[i] += feature.c1[i]
            else:
                for i in range(len(feature.c0)):
                    scores[i] += feature.c0[i]
        return [x / len(self.features) for x in scores]

    def compute_posteriors(self, example):
        scores = self.compute_scores(example)
        return [1.0 / (1.0 + math.exp(-2.0 * x * len(self.features))) for x in scores]

    def classify(self, example):
        scores = self.compute_scores(example)
        max = 0
        argmax = None
        for i in range(len(self.classes)):
            if argmax == None or max < scores[i]:
                max = scores[i]
                argmax = i
        return self.classes[argmax]

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.stderr.write('USAGE: %s <stem>\n' % sys.argv[0])
        sys.exit(1)
    classifier = Classifier(sys.argv[1])
    for line in sys.stdin.xreadlines():
        columns = line.strip().split(",")
        columns[-1] = re.sub(r'\.$', '', columns[-1].strip())
        scores = classifier.compute_posteriors([set(x.split()) for x in columns])
        for i in range(len(classifier.classes)):
            if columns[-1] == classifier.classes[i]:
                sys.stdout.write('1 ')
            else:
                sys.stdout.write('0 ')
        print " ".join([str(x) for x in scores])

