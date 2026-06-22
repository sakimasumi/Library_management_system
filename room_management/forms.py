from django import forms
from django.utils import timezone
from datetime import date
from .models import Room, RoomEquipment, RoomBooking, RoomMaintenance

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = [
            'room_name', 'room_number', 'room_type', 'capacity', 
            'location', 'facilities', 'description', 'cover_image', 'status', 'is_active'
        ]
        widgets = {
            'room_name': forms.TextInput(attrs={'class': 'form-control'}),
            'room_number': forms.TextInput(attrs={'class': 'form-control'}),
            'room_type': forms.Select(attrs={'class': 'form-control'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'facilities': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'cover_image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class RoomEquipmentForm(forms.ModelForm):
    class Meta:
        model = RoomEquipment
        fields = [
            'equipment_name', 'equipment_type', 'model_number', 
            'serial_number', 'status', 'purchase_date', 
            'warranty_expires', 'notes'
        ]
        widgets = {
            'equipment_name': forms.TextInput(attrs={'class': 'form-control'}),
            'equipment_type': forms.Select(attrs={'class': 'form-control'}),
            'model_number': forms.TextInput(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'purchase_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'warranty_expires': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class RoomBookingForm(forms.ModelForm):
    class Meta:
        model = RoomBooking
        fields = [
            'room', 'booking_date', 'start_time', 'end_time', 
            'purpose', 'attendees_count', 'notes', 'special_requirements'
        ]
        widgets = {
            'room': forms.Select(attrs={'class': 'form-control'}),
            'booking_date': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date',
                'min': timezone.now().date().strftime('%Y-%m-%d')
            }),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'purpose': forms.TextInput(attrs={'class': 'form-control'}),
            'attendees_count': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'special_requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        booking_date = cleaned_data.get('booking_date')
        room = cleaned_data.get('room')
        
        if start_time and end_time:
            if start_time >= end_time:
                raise forms.ValidationError("End time must be after start time.")
        
        if booking_date:
            if booking_date < date.today():
                raise forms.ValidationError("Booking date cannot be in the past.")
        
        # Check room capacity
        attendees_count = cleaned_data.get('attendees_count')
        if room and attendees_count:
            if attendees_count > room.capacity:
                raise forms.ValidationError(f"Number of attendees exceeds room capacity ({room.capacity}).")
        
        return cleaned_data

class RoomMaintenanceForm(forms.ModelForm):
    class Meta:
        model = RoomMaintenance
        fields = [
            'room', 'maintenance_type', 'description', 'scheduled_date', 
            'performed_by', 'cost', 'notes'
        ]
        widgets = {
            'room': forms.Select(attrs={'class': 'form-control'}),
            'maintenance_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'scheduled_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'performed_by': forms.TextInput(attrs={'class': 'form-control'}),
            'cost': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }