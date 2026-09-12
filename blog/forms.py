from django import forms
from .models import Post, Comment, Profile


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('title', 'text', 'image',)


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add a comment...'}),
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('display_name', 'real_name', 'bio', 'university', 'current_level', 'avatar')
        widgets = {
            'display_name': forms.TextInput(attrs={'placeholder': 'Name shown on your posts', 'maxlength': 100}),
            'real_name': forms.TextInput(attrs={'placeholder': 'Your real name \u2014 shown only on hover (optional)', 'maxlength': 100}),
            'bio': forms.Textarea(attrs={'rows': 3, 'placeholder': 'A short bio...', 'maxlength': 300}),
            'university': forms.TextInput(attrs={'placeholder': 'Your university (optional)', 'maxlength': 150}),
            'current_level': forms.TextInput(attrs={'placeholder': 'e.g. 300 Level (optional)', 'maxlength': 50}),
        }
