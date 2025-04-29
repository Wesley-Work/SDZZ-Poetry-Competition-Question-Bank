import poemsData from '../data/poems_v2.json';
import poemsSentencesData from '../data/poemsSentencesList.json';

interface Poem {
  id: number;
  title: string;
  author: string;
  dynasty: string;
  content: string;
  type: string;
  tags: string[];
}

export async function loadPoems(): Promise<Poem[]> {
  return poemsData;
}

export async function loadPoemsSentences(): Promise<Poem[]> {
  return poemsSentencesData;
}
