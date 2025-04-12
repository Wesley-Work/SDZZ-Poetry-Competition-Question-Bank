import poemsData from '../data/poems_v2.json';

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
  return poemsData.poems;
}
