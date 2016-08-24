from itertools import product

import sys
from django.core.management import BaseCommand
from zds.forum.models import Tag
from zds.forum.models import Topic


class ResolutionStrategy(object):
    model = Tag
    name = "unknown"

    def resolve(self, left, right):
        changed_topics = Topic.objects.filter(tags__in=[right])
        for changed_topic in changed_topics.all():
            changed_topic.tags.remove(right)
            changed_topic.tags.add(left)
            changed_topic.save()
        Tag.objects.delete(right)


class AutomaticStrategy(ResolutionStrategy):
    name = "automatic"

    def __init__(self, ltr=True):
        super(AutomaticStrategy).__init__()
        self.left_to_right = ltr

    def resolve(self, left, right):
        target = left if self.left_to_right else right
        replaced = right if self.left_to_right else left
        super(AutomaticStrategy).resolve(target, replaced)


class ManualStrategy(ResolutionStrategy):
    name = "manual"

    def __init__(self, _input, output):
        self.input = _input
        self.output = output
        super(ManualStrategy, self).__init__()

    def resolve(self, left, right):
        result = self.input.read()
        if result.strip() == "3" or result.strip().lower() == "i":
            self.output.write("{}/{} ignored".format(left, right))
        elif result.strip() == "1":
            super(ManualStrategy, self).resolve(left, right)
        elif result.strip() == "2":
            super(ManualStrategy, self).resolve(right, left)


class Command(BaseCommand):
    help = 'List all tags used in form and try to find similar ones. Then it propose you to merge tags, three choices' \
           'are given : \n' \
           '- 1 => merge the second tag into first and give update all topics with the bad tag\n' \
           '- 2 => merge the first tag into the second and give update all topics with the bad tag \n' \
           '- 3 (or i) => ignore and got to the next proposition. \n\n' \
           'if you use --merge-plural it will automaticaly send all "plural tags" into the singular ' \
           'equivalent if exists.\n' \
           'if you use --merge-single it will automaticaly send all "singular tags" into the plural equivalent' \
           'if exists.'

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--merge-plural',
            action='store_true',
            dest='plural_strategy',
            default=None,
            help='Use automatic strategy to merge plural version of tag.',
        )
        parser.add_argument(
            '--merge-singular',
            action='store_false',
            dest='plural_strategy',
            default=None,
            help='Use automatic strategy to merge singular version of tag.',
        )

    def handle(self, *args, **options):
        plural_strategy = ManualStrategy(sys.stdin, self.stdout)
        if options['plural_strategy'] is not None:
            plural_strategy = AutomaticStrategy(options['plural_strategy'])
        segment_strategy = ManualStrategy(sys.stdin, self.stdout)
        levenstein_strategy = ManualStrategy(sys.stdin, self.stdout)
        couples = {
            'plural': {'list': [], 'strategy': plural_strategy},
            'segment': {'list': [], 'strategy': segment_strategy},
            'levenstein': {'list': [], 'strategy': levenstein_strategy}
        }
        self.__iterate_plural(couples["plural"])
        self.__iterate_segment(couples["segment"])
        self.__iterate_levenstein(couples["levenstein"])
        for element, working_entity in couples.items():
            self.stdout.write('{} => {}'.format(element, working_entity['strategy'].name))
            for target, candidate in working_entity["list"]:
                working_entity["strategy"].resolve(target, candidate)

    def __iterate_plural(self, storage):
        for target, candidate in product(Tag.objects, Tag.objects):
            if target == candidate or not candidate.startswith(target):  # if there is no common word in both tags
                continue
            if not candidate.endswith("s") and not candidate.endswith("ux"):  # most common french plurals
                continue
            storage['list'].append((target, candidate))
        self.stdout.write('{} plural couples will be treated.'.format(len(storage['list'])))

    def __iterate_segment(self, storage):

        splitters = ('/', ' ', '-')
        for target, candidate in product(Tag.objects, Tag.objects):
            if candidate == target or target not in candidate:
                continue
            for splitter in splitters:
                splitted = candidate.split(splitter)
                if any([target in segment for segment in splitted]):
                    storage['list'].append((target, candidate))
                    break
        self.stdout.write('{} segment couples will be treated.'.format(len(storage['list'])))

    def __iterate_levenstein(self, storage):
        self.stdout.write('levenstein comparison is not yet implemented.')
