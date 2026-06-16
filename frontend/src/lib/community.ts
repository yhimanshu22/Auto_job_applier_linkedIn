export type CommunityReply = {
  id: number;
  post_id: number;
  parent_reply_id: number | null;
  author_name: string;
  body: string;
  created_at: string;
};

export type CommunityPost = {
  id: number;
  author_name: string;
  body: string;
  reply_count: number;
  created_at: string;
  replies: CommunityReply[];
};
